"""
DoctoAgent — Base LLM Agent
=============================
Classe de base pour tous les agents alimentés par un LLM (Gemini).

Cycle de vie d'un agent :
  1. Reçoit un contexte (dict de l'état LangGraph)
  2. Construit un message utilisateur structuré
  3. Appelle Gemini avec les outils bindés
  4. GEMINI DÉCIDE quels outils appeler
  5. Les outils sont exécutés, leurs résultats renvoyés à Gemini
  6. Gemini raisonne sur les résultats et produit une réponse JSON finale
  7. Le JSON est parsé et retourné comme dict structuré

Ce cycle est la boucle ReAct (Reasoning + Acting) :
  Think → Act (tool call) → Observe (result) → Think → ... → Respond

Auteur : Rim Hajji — PFE 2026
"""

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

from backend.database.redis_client import get_redis_sync

from dotenv import load_dotenv
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
logger = logging.getLogger("doctoagent.base_llm_agent")

GEMINI_MODEL      = "gemini-2.0-flash-lite"
GROQ_MODEL        = "llama-3.1-8b-instant"   # 500k TPD / 30k TPM vs 100k/6k pour 70b
OPENAI_MODEL      = "gpt-4o-mini"
SAMBANOVA_MODEL   = "Meta-Llama-3.3-70B-Instruct"
SAMBANOVA_BASE_URL = "https://api.sambanova.ai/v1"
CHEEBO_MODEL_PATH = os.getenv("CHEEBO_MODEL_PATH", r"C:\cheebo\cheebo-q4_k_m.gguf")
MAX_ITERATIONS    = 3
REQUEST_TIMEOUT   = 30
MAX_RETRIES       = 3
DEFAULT_RETRY_S   = 10

# LLM_PROVIDER=groq | openai | gemini | sambanova | cheebo (défaut: gemini)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()

_CIRCUIT_BREAKER_KEY = "groq_quota_exhausted"
_CIRCUIT_BREAKER_TTL = 60  # secondes

_CHEEBO_SINGLETON = None  # instance unique partagée entre tous les agents


def _get_cheebo_singleton() -> "ChatLlamaCpp":
    global _CHEEBO_SINGLETON
    if _CHEEBO_SINGLETON is not None:
        return _CHEEBO_SINGLETON
    try:
        from langchain_community.chat_models import ChatLlamaCpp
    except ImportError:
        raise ImportError("pip install llama-cpp-python langchain-community")
    _CHEEBO_SINGLETON = ChatLlamaCpp(
        model_path   = CHEEBO_MODEL_PATH,
        temperature  = 0.1,
        n_ctx        = 4096,
        n_threads    = int(os.getenv("CHEEBO_THREADS", "4")),
        n_gpu_layers = int(os.getenv("CHEEBO_GPU_LAYERS", "0")),
        verbose      = False,
    )
    logger.info(f"[Cheebo] Modèle chargé une seule fois : {CHEEBO_MODEL_PATH}")
    return _CHEEBO_SINGLETON


def _cb_is_open() -> bool:
    """Retourne True si le circuit-breaker Groq est actif (quota épuisé)."""
    try:
        return bool(get_redis_sync().exists(_CIRCUIT_BREAKER_KEY))
    except Exception:
        return False


def _cb_trip():
    """Active le circuit-breaker pour 60 s (partagé entre tous les workers)."""
    try:
        get_redis_sync().setex(_CIRCUIT_BREAKER_KEY, _CIRCUIT_BREAKER_TTL, "1")
    except Exception:
        pass


def _cb_reset():
    """Désactive le circuit-breaker après un succès."""
    try:
        get_redis_sync().delete(_CIRCUIT_BREAKER_KEY)
    except Exception:
        pass


def reset_quota_breaker():
    """Compatibilité : réinitialise le circuit-breaker (no-op si Redis gère le TTL)."""
    _cb_reset()


# ──────────────────────────────────────────────────────────────────
# BASE LLM AGENT
# ──────────────────────────────────────────────────────────────────
class BaseLLMAgent:
    """
    Agent LLM générique : Gemini + outils + boucle ReAct.

    Chaque agent spécialisé hérite de cette classe et définit :
    - system_prompt  : rôle et instructions précises de l'agent
    - tools          : liste d'outils LangChain que le LLM peut appeler
    - use_llm        : False → utilise directement le fallback (économise quota)
    - _build_prompt  : construit le message HumanMessage depuis le contexte
    - _parse_output  : transforme la réponse JSON en dict structuré
    """

    name          : str = "BaseLLMAgent"
    system_prompt : str = ""
    tools         : List[BaseTool] = []
    use_llm       : bool = True   # Mettre False pour bypasser Gemini

    def __init__(self):
        if LLM_PROVIDER == "groq":
            self.llm = self._init_groq()
        elif LLM_PROVIDER == "openai":
            self.llm = self._init_openai()
        elif LLM_PROVIDER == "sambanova":
            self.llm = self._init_sambanova()
        elif LLM_PROVIDER == "cheebo":
            self.llm = self._init_cheebo()
        else:
            self.llm = self._init_gemini()

        self.llm_with_tools = self.llm.bind_tools(self.tools) if self.tools else self.llm
        self.tools_map       = {t.name: t for t in self.tools}
        logger.info(
            f"[{self.name}] Initialisé ({LLM_PROVIDER}) avec {len(self.tools)} outils : "
            f"{list(self.tools_map.keys())}"
        )

    def _init_gemini(self):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning(f"[{self.name}] GEMINI_API_KEY manquante — fallback activé")
        return ChatGoogleGenerativeAI(
            model          = GEMINI_MODEL,
            temperature    = 0,
            google_api_key = api_key,
            max_retries    = 0,
            request_timeout= REQUEST_TIMEOUT,
        )

    def _init_openai(self):
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            logger.error("[BaseLLMAgent] langchain-openai non installé — pip install langchain-openai")
            return self._init_gemini()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning(f"[{self.name}] OPENAI_API_KEY manquante — basculement sur Gemini")
            return self._init_gemini()
        logger.info(f"[{self.name}] OpenAI activé ({OPENAI_MODEL})")
        return ChatOpenAI(
            model       = OPENAI_MODEL,
            temperature = 0,
            api_key     = api_key,
            max_retries = 0,
            timeout     = REQUEST_TIMEOUT,
        )

    def _init_groq(self):
        try:
            from langchain_groq import ChatGroq
        except ImportError:
            logger.error("[BaseLLMAgent] langchain-groq non installé — pip install langchain-groq")
            return self._init_gemini()
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logger.warning(f"[{self.name}] GROQ_API_KEY manquante — basculement sur Gemini")
            return self._init_gemini()
        logger.info(f"[{self.name}] Groq activé ({GROQ_MODEL})")
        return ChatGroq(
            model       = GROQ_MODEL,
            temperature = 0,
            groq_api_key= api_key,
            max_retries = 0,
        )

    def _init_cheebo(self):
        if not os.path.exists(CHEEBO_MODEL_PATH):
            logger.warning(f"[{self.name}] Modèle Cheebo introuvable : {CHEEBO_MODEL_PATH} — basculement sur Gemini")
            return self._init_gemini()
        try:
            llm = _get_cheebo_singleton()
            logger.info(f"[{self.name}] Cheebo activé ({CHEEBO_MODEL_PATH})")
            return llm
        except Exception as e:
            logger.error(f"[{self.name}] Erreur chargement Cheebo : {e} — basculement sur Gemini")
            return self._init_gemini()

    def _init_sambanova(self):
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            logger.error("[BaseLLMAgent] langchain-openai non installé — pip install langchain-openai")
            return self._init_gemini()
        api_key = os.getenv("SAMBANOVA_API_KEY")
        if not api_key:
            logger.warning(f"[{self.name}] SAMBANOVA_API_KEY manquante — basculement sur Gemini")
            return self._init_gemini()
        logger.info(f"[{self.name}] SambaNova activé ({SAMBANOVA_MODEL})")
        return ChatOpenAI(
            model       = SAMBANOVA_MODEL,
            temperature = 0.1,
            api_key     = api_key,
            base_url    = SAMBANOVA_BASE_URL,
            max_retries = 0,
            timeout     = REQUEST_TIMEOUT,
        )

    # ─────────────────────────────────────────
    # Interface publique
    # ─────────────────────────────────────────
    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Point d'entrée principal. Exécute la boucle ReAct complète.
        Retourne toujours un dict (jamais d'exception propagée).
        """
        start = time.perf_counter()
        if not self.use_llm:
            logger.info(f"[{self.name}] LLM désactivé → fallback KB direct")
            result = self._fallback(context)
        else:
            try:
                result = self._react_loop(context)
            except Exception as exc:
                logger.error(f"[{self.name}] Erreur critique : {exc}", exc_info=True)
                result = self._fallback(context, error=str(exc))

        result["_agent_name"]      = self.name
        result["_processing_ms"]   = round((time.perf_counter() - start) * 1000, 2)
        return result

    # ─────────────────────────────────────────
    # Boucle ReAct (Reasoning + Acting)
    # ─────────────────────────────────────────
    def _react_loop(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Boucle principale :
          1. Construire le message initial
          2. Gemini répond (peut appeler des outils ou répondre directement)
          3. Si tool calls → exécuter, renvoyer résultats → retour en 2
          4. Si réponse finale → parser le JSON
        """
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=self._build_prompt(context)),
        ]

        for iteration in range(MAX_ITERATIONS):
            logger.debug(f"[{self.name}] Iteration {iteration + 1}/{MAX_ITERATIONS}")

            try:
                response = self._invoke_with_retry(messages)
            except Exception as exc:
                err_str = str(exc)
                is_tool_err = (
                    "tool_use_failed" in err_str
                    or "tool call validation failed" in err_str
                    or ("400" in err_str and "tool" in err_str.lower())
                )
                if is_tool_err:
                    logger.warning(f"[{self.name}] Tool call rejeté par l'API — fallback: {err_str[:120]}")
                    return self._fallback(context, error="tool_call_error")
                raise
            messages.append(response)

            # Si Gemini n'appelle pas d'outils → réponse finale
            if not getattr(response, "tool_calls", None):
                logger.info(f"[{self.name}] Réponse finale après {iteration + 1} iteration(s)")
                return self._parse_output(response.content, context)

            # Gemini a décidé d'appeler des outils → les exécuter
            tool_messages = self._execute_tool_calls(response.tool_calls)
            messages.extend(tool_messages)
            logger.info(
                f"[{self.name}] {len(response.tool_calls)} outil(s) appelé(s) : "
                f"{[tc['name'] for tc in response.tool_calls]}"
            )

        # Limite d'itérations atteinte → force-finalize sans outils
        logger.warning(f"[{self.name}] Limite {MAX_ITERATIONS} itérations atteinte")
        try:
            messages.append(HumanMessage(content="Génère le JSON final. Aucun outil supplémentaire."))
            final = self.llm.invoke(messages)
            if final.content:
                parsed = self._parse_output(final.content, context)
                if parsed.get("status") != "fallback":
                    logger.info(f"[{self.name}] Force-finalize réussi")
                    return parsed
        except Exception as e:
            logger.warning(f"[{self.name}] Force-finalize échoué : {e}")

        last_ai = next((m for m in reversed(messages) if isinstance(m, AIMessage)), None)
        return self._parse_output(last_ai.content if last_ai else "", context)

    # ─────────────────────────────────────────
    # Appel Gemini avec retry sur 429
    # ─────────────────────────────────────────
    def _invoke_with_retry(self, messages: list):
        """Appelle le LLM et réessaie sur 429 (quota) et 503 (surcharge temporaire)."""
        if _cb_is_open():
            raise RuntimeError(f"[{self.name}] Quota journalier déjà épuisé — fallback immédiat")

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                result = self.llm_with_tools.invoke(messages)
                _cb_reset()  # succès → désactive le circuit-breaker si actif
                return result
            except Exception as exc:
                err_str = str(exc)

                # SambaNova/Llama : répond parfois en JSON directement dans un tool call sans 'name'
                # → l'API rejette avec 400 mais error_model_output contient la vraie réponse
                if ('"name" keyword does not appear' in err_str
                        or "Invalid function calling output" in err_str):
                    return self._recover_malformed_tool_call(exc)

                is_429 = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "rate_limit" in err_str.lower()
                is_503 = "503" in err_str or "UNAVAILABLE" in err_str

                # Quota journalier épuisé → circuit-breaker Redis + fallback immédiat
                # Détecte : Gemini (limit: 0), Groq TPD ("tokens per day"), retry > 5 min
                # (?!s) exclut "ms" (millisecondes) pour ne pas confondre "320ms" avec "320m"
                _retry_min = re.search(r"try again in (\d+)m(?!s)", err_str, re.IGNORECASE)
                quota_zero = (
                    "limit: 0" in err_str
                    or "GenerateRequestsPerDayPerProject" in err_str
                    or "tokens per day" in err_str.lower()
                    or (_retry_min and int(_retry_min.group(1)) >= 5)
                )

                if quota_zero:
                    _cb_trip()
                    logger.error(f"[{self.name}] Quota journalier épuisé — circuit-breaker Redis activé 60s, fallback immédiat")
                    raise

                if (is_429 or is_503) and attempt < MAX_RETRIES:
                    if is_429:
                        # Groq répond: "Please try again in 1.8s" ou "retry after Xs"
                        match = re.search(
                            r"(?:try\s+again\s+in|retry[_\s]+(?:after|in))\s*([\d]+(?:\.\d+)?)\s*s",
                            err_str, re.IGNORECASE,
                        )
                        default_wait = 5 if LLM_PROVIDER == "groq" else DEFAULT_RETRY_S
                        wait = float(match.group(1)) + 1 if match else default_wait
                        logger.warning(
                            f"[{self.name}] 429 rate limit ({LLM_PROVIDER}) — "
                            f"attente {wait:.0f}s avant retry {attempt}/{MAX_RETRIES - 1}"
                        )
                    else:
                        wait = 8
                        logger.warning(
                            f"[{self.name}] 503 UNAVAILABLE (surcharge) — "
                            f"attente {wait}s avant retry {attempt}/{MAX_RETRIES - 1}"
                        )
                    time.sleep(wait)
                else:
                    raise

    # ─────────────────────────────────────────
    # Récupération tool call malformé (Llama)
    # ─────────────────────────────────────────
    def _recover_malformed_tool_call(self, exc) -> AIMessage:
        """
        SambaNova/Llama produit parfois la réponse finale dans un tool call sans champ 'name'.
        L'API renvoie 400 mais inclut error_model_output avec le vrai contenu du modèle.
        On extrait ce contenu et on le retourne comme AIMessage normal.
        """
        raw = None

        # 1. Via exc.body (openai SDK — le plus fiable)
        body = getattr(exc, "body", None)
        if isinstance(body, dict):
            raw = body.get("error_model_output")

        # 2. Fallback : regex sur la repr str de l'exception
        if not raw:
            err_str = str(exc)
            match = re.search(
                r"'error_model_output':\s*'((?:[^'\\]|\\.)*)'",
                err_str, re.DOTALL,
            )
            if match:
                raw = match.group(1).replace("\\'", "'").replace("\\n", "\n")

        if raw:
            logger.info(
                f"[{self.name}] Réponse finale récupérée depuis error_model_output "
                f"(Llama tool-call sans nom)"
            )
            return AIMessage(content=raw)

        raise exc

    # ─────────────────────────────────────────
    # Exécution des outils
    # ─────────────────────────────────────────
    def _execute_tool_calls(self, tool_calls: list) -> List[ToolMessage]:
        """Exécute tous les tool calls retournés par Gemini."""
        results = []
        for tc in tool_calls:
            tool_name = tc.get("name", "")
            tool_args = tc.get("args", {})
            tool_id   = tc.get("id", tool_name)

            tool_fn = self.tools_map.get(tool_name)
            if not tool_fn:
                content = f"Outil '{tool_name}' non trouvé."
                logger.error(f"[{self.name}] {content}")
            else:
                try:
                    content = str(tool_fn.invoke(tool_args))
                    logger.debug(
                        f"[{self.name}] Tool '{tool_name}' → "
                        f"{content[:80]}..."
                    )
                except Exception as e:
                    content = f"Erreur lors de l'exécution de '{tool_name}' : {e}"
                    logger.error(f"[{self.name}] {content}")

            results.append(ToolMessage(content=content, tool_call_id=tool_id))
        return results

    # ─────────────────────────────────────────
    # Parsing JSON de la réponse
    # ─────────────────────────────────────────
    def _extract_json(self, text) -> Optional[Dict]:
        """
        Extrait le JSON de la réponse Gemini.
        Gère les cas : JSON pur, JSON dans ```json...```, JSON avec texte autour.
        Gère aussi le cas où content est une liste de blocs (langchain-google-genai 4.x).
        """
        if not text:
            return None

        # Normaliser : si content est une liste de blocs, extraire le texte
        if isinstance(text, list):
            parts = []
            for block in text:
                if isinstance(block, dict):
                    parts.append(block.get("text", ""))
                else:
                    parts.append(str(block))
            text = " ".join(parts)

        if not text:
            return None

        # 1. Retirer les blocs markdown ```json ... ```
        clean = text.strip()
        if "```json" in clean:
            clean = clean.split("```json", 1)[1]
            clean = clean.split("```", 1)[0].strip()
        elif "```" in clean:
            clean = clean.split("```", 1)[1]
            clean = clean.split("```", 1)[0].strip()

        # 2. Trouver le premier { et décoder avec raw_decode (ignore le texte après le JSON)
        start = clean.find("{")
        if start != -1:
            try:
                result, _ = json.JSONDecoder().raw_decode(clean[start:])
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"[{self.name}] JSON parse error : {e}")

        return None

    # ─────────────────────────────────────────
    # À surcharger dans chaque agent
    # ─────────────────────────────────────────
    def _build_prompt(self, context: Dict[str, Any]) -> str:
        """Construit le message HumanMessage depuis le contexte de l'état."""
        return json.dumps(context, ensure_ascii=False, indent=2, default=str)

    def _parse_output(self, raw: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Parse la réponse finale de Gemini en dict structuré."""
        parsed = self._extract_json(raw)
        if parsed:
            return parsed
        logger.warning(f"[{self.name}] JSON non parsé, fallback activé")
        return self._fallback(context, error="JSON parse failed")

    def _fallback(self, context: Dict[str, Any], error: str = "") -> Dict[str, Any]:
        """Résultat de secours si l'agent échoue."""
        return {
            "status" : "fallback",
            "error"  : error,
            "message": f"Agent {self.name} indisponible. Résultat de secours utilisé.",
        }
