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

from dotenv import load_dotenv
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()
logger = logging.getLogger("doctoagent.base_llm_agent")

GEMINI_MODEL    = "gemini-2.0-flash-lite"
GROQ_MODEL      = "llama-3.3-70b-versatile"
MAX_ITERATIONS  = 2   # 1 tour outils + 1 tour réponse finale
REQUEST_TIMEOUT = 30  # secondes max par appel LLM
MAX_RETRIES     = 3   # tentatives max sur erreur quota
DEFAULT_RETRY_S = 10  # attente par défaut entre retries

# LLM_PROVIDER=groq dans .env pour utiliser Groq au lieu de Gemini
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()


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

        # Limite d'itérations atteinte → utiliser le dernier AIMessage (pas un ToolMessage)
        logger.warning(f"[{self.name}] Limite {MAX_ITERATIONS} itérations atteinte")
        last_ai = next((m for m in reversed(messages) if isinstance(m, AIMessage)), None)
        return self._parse_output(last_ai.content if last_ai else "", context)

    # ─────────────────────────────────────────
    # Appel Gemini avec retry sur 429
    # ─────────────────────────────────────────
    def _invoke_with_retry(self, messages: list):
        """Appelle le LLM et réessaie sur 429 (quota) et 503 (surcharge temporaire)."""
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return self.llm_with_tools.invoke(messages)
            except Exception as exc:
                err_str = str(exc)
                is_429 = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "rate_limit" in err_str.lower()
                is_503 = "503" in err_str or "UNAVAILABLE" in err_str

                # Quota journalier épuisé (limit: 0) → inutile d'attendre, fallback immédiat
                quota_zero = "limit: 0" in err_str or "GenerateRequestsPerDayPerProject" in err_str

                if (is_429 or is_503) and attempt < MAX_RETRIES and not quota_zero:
                    if is_429:
                        match = re.search(r"retry[_\s]+(?:after|in)[_\s]+([\d]+(?:\.\d+)?)\s*s", err_str, re.IGNORECASE)
                        default_wait = 10 if LLM_PROVIDER == "groq" else DEFAULT_RETRY_S
                        wait = float(match.group(1)) + 2 if match else default_wait
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
                    if quota_zero:
                        logger.error(f"[{self.name}] Quota journalier épuisé (limit: 0) — fallback immédiat")
                    raise

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

        # 2. Trouver le premier { et le dernier }
        start = clean.find("{")
        end   = clean.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(clean[start : end + 1])
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
