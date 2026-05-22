"""
GroqGuard — Groq comme gardien de qualité et fallback conversationnel.
=======================================================================
Deux rôles :

  1. FALLBACK  : Quand le pipeline ne peut pas analyser (symptômes / animal / durée
                 manquants), Groq génère une réponse Cheebo-style contextuelle et
                 chaleureuse à la place des templates statiques.

  2. QUALITY CHECK : Quand le pipeline répond, Groq valide la salutation / le ton
                     empathique et améliore si nécessaire. Le contenu médical est
                     TOUJOURS préservé à l'identique.

Toujours Groq (llama-3.3-70b-versatile), indépendamment du LLM_PROVIDER principal.
Timeout 6 s — si dépassé, la réponse originale est conservée sans latence supplémentaire.

Auteur : Rim Hajji — PFE 2026
"""

import asyncio
import logging
import os
import re
from typing import List, Optional

# ─── Filtre anti-numéros de téléphone ────────────────────────────────────────

_PHONE_RE = re.compile(
    r"""
    (?:                          # préfixe international optionnel
        \+\d{1,3}[\s\-\.]?
    )?
    (?:                          # groupes de chiffres séparés par espace/tiret/point
        \d{2}[\s\-\.]?
    ){4,7}
    \d{2}                        # dernier groupe obligatoire
    """,
    re.VERBOSE,
)

def _strip_phones(text: str) -> str:
    """Supprime tout numéro de téléphone du texte généré par Groq."""
    cleaned = _PHONE_RE.sub("", text)
    # Nettoyer les lignes vides ou les bullets vides laissés par la suppression
    lines = []
    for line in cleaned.splitlines():
        stripped = line.strip()
        # Ignorer les lignes qui ne contenaient que le numéro (bullet vide, tiret seul…)
        if stripped in ("•", "-", "*", "·", "–", "—", ""):
            if not stripped:
                lines.append("")
            continue
        lines.append(line)
    # Supprimer les doubles lignes vides consécutives
    result = re.sub(r"\n{3,}", "\n\n", "\n".join(lines))
    return result.strip()

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
logger = logging.getLogger("doctoagent.groq_guard")

_GROQ_MODEL        = "llama-3.1-8b-instant"   # 500k TPD — cohérent avec base_llm_agent
_TIMEOUT_S         = 15      # secondes — generate_response a besoin de plus de temps
_TIMEOUT_QUALITY_S = 6       # timeout plus court pour quality_check
_MIN_RATIO         = 0.50    # quality-check : résultat < 50 % de l'original → rejeté


# ─── Prompts ──────────────────────────────────────────────────────────────────

_SYSTEM = (
    "Tu es Cheebo, un assistant vétérinaire IA empathique et professionnel. "
    "Tu t'exprimes toujours dans la langue de l'utilisateur (français par défaut). "
    "Ton ton est rassurant et bienveillant — adapté à la gravité de la situation. "
    "Tu utilises 1 à 2 emojis par réponse maximum. "
    "Tu ne poses jamais plusieurs questions en même temps — une seule à la fois. "
    "INTERDIT ABSOLU : ne jamais dire 'je suis heureux', 'je suis ravi', 'je suis content', "
    "'I am happy', 'I am glad', 'I am pleased', 'أنا سعيد' dans n'importe quel contexte médical. "
    "Quand l'utilisateur décrit des symptômes ou une urgence, exprime de l'EMPATHIE et de la PRÉOCCUPATION, jamais de la joie. "
    "INTERDIT ABSOLU : ne jamais écrire de numéro de téléphone, de nom de clinique ou de vétérinaire dans tes réponses — "
    "ces informations sont affichées séparément par le système en cartes vérifiées."
)

_FALLBACK_PROMPT = """\
L'utilisateur vient d'écrire ce message à Cheebo (assistant vétérinaire IA) :
"{user_message}"

Langue détectée : {language}
Animal mentionné : {animal}
Historique récent : {history_summary}

Le message ne contient pas de description de symptômes vétérinaires.

Génère UNE réponse courte (2-3 phrases max) qui :
1. Reconnaît brièvement ce que l'utilisateur a dit si pertinent (un mot suffit).
2. Demande TOUJOURS les SYMPTÔMES en priorité absolue — jamais l'animal ou la durée tant que les symptômes ne sont pas décrits.
3. Reste empathique et professionnel.
4. Utilise la langue de l'utilisateur.

N'exprime JAMAIS de joie ou de bonheur face à des symptômes. Exprime de l'empathie et de la préoccupation.
Réponds directement en texte simple — pas de JSON, pas de balises markdown.\
"""

_CONTEXTUAL_REPLY_PROMPT = """\
Tu es Cheebo, assistant vétérinaire IA chaleureux et empathique.

Historique récent de la conversation :
{history_summary}

Dernier message de l'utilisateur : "{user_message}"
Langue : {language}

Réponds naturellement en 2-3 phrases max, adapté au type de message :
- Question sur l'analyse ("c'est grave ?", "que faire ?", "est-ce dangereux ?") → réponds précisément en te basant sur l'historique médical.
- Remerciement ou message positif → réponds chaleureusement et reste disponible.
- Confirmation d'action (vet contacté, départ en clinique) → félicite et souhaite un bon rétablissement.
- Amélioration de l'animal → exprime ta joie et rappelle de surveiller.
- Message hors-sujet médical → réponds brièvement et redirige vers la santé de l'animal.
- Si l'historique mentionne un animal spécifique → fais-y référence.
- Utilise la langue de l'utilisateur. 1 emoji max.

INTERDIT : ne jamais dire "je suis heureux/ravi/content" ou équivalent dans d'autres langues.
Texte direct uniquement — pas de JSON, pas de markdown.\
"""

_QUALITY_PROMPT = """\
Voici la réponse générée par le pipeline vétérinaire Cheebo :

---
{response_text}
---

Message original de l'utilisateur : "{user_message}"
Niveau d'urgence : {level}

Ta mission (STRICTE) :
• Vérifie si l'introduction / la salutation est chaleureuse et empathique pour le contexte.
• Le contenu médical (symptômes, conseils, actions, signes d'alarme)
  doit être préservé À L'IDENTIQUE — mot pour mot.

Règle de décision :
  → Si la réponse est déjà bien formulée, réponds UNIQUEMENT avec le mot : OK
  → Si seulement l'introduction doit être améliorée, retourne la réponse COMPLÈTE améliorée.

N'ajoute PAS de nouvelles informations médicales. Ne reformule PAS les conseils.
INTERDIT ABSOLU : ne jamais écrire de numéro de téléphone, de nom de clinique ou de vétérinaire.
Si la réponse originale en contient, supprime-les avant de retourner le résultat.\
"""

_TITLE_PROMPT = """\
Génère un TITRE COURT (4 à 6 mots maximum) pour cette consultation vétérinaire.

Résumé de la conversation :
{conversation_summary}
Langue : {language}

Le titre doit mentionner l'animal (si connu) et le problème principal.

Exemples de bons titres :
- "Chien — vomissements depuis 2 jours"
- "Chat léthargique et anorexique"
- "Dog limping, possible fracture"
- "Lapin — urgence respiratoire"
- "كلب — قيء منذ يومين"

Retourne UNIQUEMENT le titre, sans guillemets, sans explication, sans point final.\
"""

_VIDEO_SYNTHESIS_PROMPT = """\
Tu es un assistant vétérinaire qui analyse une vidéo d'un animal de compagnie.

Voici les descriptions de {n_frames} images extraites de la vidéo, dans l'ordre chronologique :
{frame_descriptions}

Synthétise ces observations en 3-4 phrases médicalement pertinentes :
1. Espèce probable et état général de l'animal
2. Comportement, mouvement, posture et respiration dans le temps
3. Anomalies physiques visibles (plaie, boiterie, gonflement, tremblements, etc.)
4. Évolution au fil de la vidéo (stable, s'aggrave, varie)

Sois précis et factuel. Si une frame n'est pas claire, ignore-la.
Réponds en {language}. Texte direct uniquement — pas de JSON, pas de titres.\
"""

_GENERATE_PROMPT = """\
Tu es Cheebo, assistant vétérinaire IA empathique et professionnel.

Message de l'utilisateur : "{user_message}"
Langue : {language}
Animal : {animal}
Niveau d'urgence : {urgency_level}

Données médicales analysées par le pipeline :
• Symptômes : {symptoms}
• Conditions possibles : {conditions}
• Soins à domicile : {home_care}
• Signes d'alarme : {monitoring}
• Quand consulter : {when_to_consult}
{diet_section}
Génère une réponse conversationnelle complète en {language} avec :
- Une introduction EMPATHIQUE adaptée au niveau d'urgence ({urgency_tone}) — jamais "je suis heureux/ravi/content"
- Les conditions possibles mentionnées SANS diagnostic ferme
- Les conseils de soin concrets sous forme de liste à puces
- Les signes d'alarme à surveiller
- Quand consulter le vétérinaire (sans mentionner de noms ni numéros)
- Markdown : **gras**, •, _italique_
- 1 à 2 emojis maximum
- Termine par "_Ces conseils ne remplacent pas l'avis d'un vétérinaire._"

INTERDITS ABSOLUS :
- Ne jamais exprimer de joie ou bonheur face aux symptômes décrits.
- Ne JAMAIS citer de noms de cliniques, de vétérinaires ou de numéros de téléphone — le système les affiche séparément en cartes cliquables vérifiées.
Réponds en texte direct, PAS de JSON.\
"""


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _history_summary(history: list) -> str:
    if not history:
        return "Début de conversation."
    parts = []
    for m in history[-4:]:
        role = "Utilisateur" if getattr(m, "role", "") == "user" else "Cheebo"
        has_images = getattr(m, "has_images", False)
        content = getattr(m, "content", str(m))
        if has_images and role == "Utilisateur":
            display = "[a envoyé une ou plusieurs photos de l'animal pour analyse]"
        else:
            display = content[:80]
        parts.append(f"{role}: {display}")
    return " | ".join(parts)


# ─── Fallback statique (si Groq indisponible) ────────────────────────────────

def _build_static_response(data: dict) -> str:
    """Réponse de secours sans LLM — utilisée si Groq est down ou timeout."""
    level    = data.get("urgency", {}).get("level", "LOW")
    rec      = data.get("recommendation", {})
    care     = data.get("care_plan", {})
    preds    = data.get("predictions", {})

    headers = {
        "CRITICAL": "🚨 **URGENCE CRITIQUE**",
        "HIGH"    : "⚠️ **Situation préoccupante**",
        "MODERATE": "📋 **Surveillance recommandée**",
        "LOW"     : "✅ **Situation bénigne**",
    }
    lines = [headers.get(level, "📋 **Analyse**"), ""]

    msg = rec.get("message", "")
    if msg:
        lines += [msg, ""]

    assocs = [a for a in preds.get("possible_associations", []) if isinstance(a, dict) and a.get("condition")]
    if assocs:
        lines.append("**🔍 Pistes possibles :**")
        for a in assocs[:3]:
            line = f"• **{a['condition']}**"
            if a.get("watch_for"):
                line += f" — surveiller : {a['watch_for']}"
            lines.append(line)
        lines.append("")

    home_care = care.get("home_care_steps", []) or rec.get("actions", [])
    if home_care:
        lines.append("**💊 Soins à domicile :**")
        for c in home_care[:4]:
            lines.append(f"• {c}")
        lines.append("")

    when = care.get("when_to_consult", "") or rec.get("next_steps", "")
    if when:
        lines += [f"📅 **Quand consulter** : {when}", ""]

    monitoring = care.get("monitoring_signs", [])
    if monitoring:
        lines.append("👁️ **Signes d'alarme :**")
        for s in monitoring[:3]:
            lines.append(f"• {s}")
        lines.append("")

    lines.append("_Ces conseils ne remplacent pas l'avis d'un vétérinaire._")
    return "\n".join(lines)


# ─── GroqGuard ────────────────────────────────────────────────────────────────

class GroqGuard:
    """
    Gardien de qualité et fallback conversationnel basé sur Groq.
    Utilise toujours Groq, quel que soit le LLM_PROVIDER principal.
    """

    def __init__(self):
        self._llm = None
        try:
            from langchain_groq import ChatGroq
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                logger.warning("[GroqGuard] GROQ_API_KEY manquante — garde désactivée")
                return
            self._llm = ChatGroq(
                model        = _GROQ_MODEL,
                temperature  = 0.35,
                groq_api_key = api_key,
                max_retries  = 0,
            )
            logger.info(f"[GroqGuard] Initialisé ({_GROQ_MODEL})")
        except ImportError:
            logger.error("[GroqGuard] langchain-groq non installé — garde désactivée")

    @property
    def available(self) -> bool:
        return self._llm is not None

    # ── Appel synchrone (exécuté dans un thread executor) ─────────────────────
    def _call(self, user_prompt: str) -> str:
        from langchain_core.messages import HumanMessage, SystemMessage
        resp = self._llm.invoke([
            SystemMessage(content=_SYSTEM),
            HumanMessage(content=user_prompt),
        ])
        return resp.content.strip()

    async def _call_async(self, prompt: str, timeout: float = _TIMEOUT_S) -> Optional[str]:
        """Appel asynchrone avec timeout. Retourne None en cas d'échec."""
        loop = asyncio.get_running_loop()
        try:
            result = await asyncio.wait_for(
                loop.run_in_executor(None, self._call, prompt),
                timeout=timeout,
            )
            # Filtre de sécurité : retire tout numéro de téléphone quelle que soit la raison
            return _strip_phones(result) if result else result
        except asyncio.TimeoutError:
            logger.warning("[GroqGuard] Timeout dépassé — réponse originale conservée")
            return None
        except Exception as exc:
            logger.warning(f"[GroqGuard] Erreur Groq : {exc}")
            return None

    # ── API publique ───────────────────────────────────────────────────────────

    async def fallback_response(
        self,
        user_message: str,
        language    : str,
        entities    : list,
        history     : list,
    ) -> Optional[str]:
        """
        Génère une réponse Cheebo-style quand le pipeline ne peut pas analyser.
        Retourne None si Groq est indisponible → le caller utilise les templates statiques.
        """
        if not self.available:
            return None

        animals    = [e["text"] for e in entities if e.get("label") == "ANIMAL"]
        animal_str = animals[0] if animals else "non mentionné"

        prompt = _FALLBACK_PROMPT.format(
            user_message    = user_message,
            language        = language,
            animal          = animal_str,
            history_summary = _history_summary(history),
        )

        result = await self._call_async(prompt)
        if result:
            logger.info(f"[GroqGuard] Fallback généré ({len(result)} chars)")
        return result

    async def generate_response(
        self,
        pipeline_data: dict,
        user_message : str,
    ) -> str:
        """
        Génère directement la réponse finale Cheebo à partir des données du pipeline.
        Remplace SynthesisAgent — Groq produit un texte conversationnel naturel.
        Retourne le fallback statique si Groq est indisponible ou timeout.
        """
        fallback = _build_static_response(pipeline_data)
        if not self.available:
            return fallback

        analysis   = pipeline_data.get("analysis", {})
        urgency    = pipeline_data.get("urgency", {})
        symptoms   = pipeline_data.get("symptoms", {})
        predictions = pipeline_data.get("predictions", {})
        care       = pipeline_data.get("care_plan", {})
        emergency  = pipeline_data.get("emergency", {})
        rec        = pipeline_data.get("recommendation", {})

        language      = analysis.get("language", "fr")
        animal        = symptoms.get("animal", "votre animal")
        urgency_level = urgency.get("level", "LOW")
        syms          = symptoms.get("symptoms_normalized", []) or symptoms.get("symptoms_detected", [])
        conditions    = [
            a.get("condition", "") for a in predictions.get("possible_associations", [])[:3]
            if isinstance(a, dict) and a.get("condition")
        ]
        home_care_steps = care.get("home_care_steps", []) or rec.get("actions", [])
        monitoring      = care.get("monitoring_signs", [])
        when_to_consult = care.get("when_to_consult", "") or rec.get("next_steps", "")
        diet            = care.get("diet_advice")
        vets            = emergency.get("partner_vets", []) if emergency.get("is_emergency") else []

        tone_map = {
            "CRITICAL": "URGENT — ton alarmant justifié, situation critique",
            "HIGH"    : "préoccupé mais rassurant, consultation urgente requise",
            "MODERATE": "attentif et rassurant, surveillance recommandée",
            "LOW"     : "rassurant et bienveillant, situation bénigne",
        }

        diet_section = f"• Alimentation : {diet}\n" if diet else ""

        # Si le pipeline n'a pas pu extraire les symptômes (souvent pour l'arabe),
        # indiquer à Groq d'analyser directement depuis le message utilisateur.
        if syms:
            symptoms_str = ", ".join(syms)
        else:
            symptoms_str = f"[non extraits — analyser depuis le message : \"{user_message[:120]}\"]"

        prompt = _GENERATE_PROMPT.format(
            user_message    = user_message,
            language        = language,
            animal          = animal,
            urgency_level   = urgency_level,
            urgency_tone    = tone_map.get(urgency_level, tone_map["LOW"]),
            symptoms        = symptoms_str,
            conditions      = ", ".join(conditions) if conditions else "à déterminer depuis le message",
            home_care       = " | ".join(home_care_steps[:4]) if home_care_steps else "repos et surveillance",
            monitoring      = " | ".join(monitoring[:3]) if monitoring else "tout changement d'état",
            when_to_consult = when_to_consult or "si les symptômes persistent ou s'aggravent",
            diet_section    = diet_section,
        )

        result = await self._call_async(prompt, timeout=_TIMEOUT_S)
        if result and len(result.strip()) > 30:
            logger.info(f"[GroqGuard] Réponse générée ({len(result)} chars)")
            return result.strip()

        logger.warning("[GroqGuard] generate_response échoué — fallback statique")
        return fallback

    async def contextual_reply(
        self,
        user_message: str,
        language    : str,
        history     : list,
    ) -> Optional[str]:
        """
        Génère une réponse courte et contextuelle pour les messages conversationnels
        (remerciements, confirmations d'action, clôtures, améliorations).
        Connaît l'historique → peut référencer l'animal et la situation.
        Retourne None si Groq est indisponible.
        """
        if not self.available:
            return None

        prompt = _CONTEXTUAL_REPLY_PROMPT.format(
            user_message    = user_message,
            language        = language,
            history_summary = _history_summary(history),
        )

        result = await self._call_async(prompt, timeout=_TIMEOUT_QUALITY_S)
        if result:
            logger.info(f"[GroqGuard] Réponse contextuelle générée ({len(result)} chars)")
        return result

    async def synthesize_video_frames(
        self,
        frame_descriptions: list,
        language: str = "fr",
    ) -> str:
        """
        Synthétise les descriptions de N frames vidéo en une observation médicale temporelle.
        Retourne une concaténation simple si Groq est indisponible.
        """
        if not self.available or not frame_descriptions:
            return " | ".join(frame_descriptions) if frame_descriptions else "Vidéo analysée."

        numbered = "\n".join(f"Frame {i+1}: {d}" for i, d in enumerate(frame_descriptions))
        prompt = _VIDEO_SYNTHESIS_PROMPT.format(
            n_frames          = len(frame_descriptions),
            frame_descriptions = numbered,
            language          = language,
        )
        result = await self._call_async(prompt, timeout=_TIMEOUT_S)
        if result and len(result.strip()) > 20:
            logger.info(f"[GroqGuard] Synthèse vidéo générée ({len(result)} chars)")
            return result.strip()
        return " | ".join(frame_descriptions)

    async def quality_check(
        self,
        response_text: str,
        user_message : str,
        level        : str,
    ) -> str:
        """
        Valide et améliore (si nécessaire) la salutation / intro de la réponse pipeline.
        Retourne toujours une réponse valide (originale si Groq échoue, timeout ou dit OK).
        """
        if not self.available or not response_text:
            return response_text

        prompt = _QUALITY_PROMPT.format(
            response_text = response_text,
            user_message  = user_message,
            level         = level,
        )

        result = await self._call_async(prompt, timeout=_TIMEOUT_QUALITY_S)
        if not result:
            return response_text

        # Groq a jugé la réponse bonne telle quelle
        if result.strip().upper() == "OK":
            logger.info("[GroqGuard] Quality check: réponse validée (OK)")
            return response_text

        # Sécurité : résultat trop court → Groq a probablement tronqué le contenu médical
        if len(result) < len(response_text) * _MIN_RATIO:
            logger.warning("[GroqGuard] Quality check: résultat trop court — original conservé")
            return response_text

        logger.info(f"[GroqGuard] Quality check: réponse améliorée ({len(result)} chars)")
        return result

    async def generate_title(self, conversation_summary: str, language: str) -> Optional[str]:
        """Génère un titre court (4-6 mots) pour une conversation vétérinaire."""
        if not self.available:
            return None
        prompt = _TITLE_PROMPT.format(
            conversation_summary=conversation_summary,
            language=language,
        )
        result = await self._call_async(prompt, timeout=5.0)
        if result and 3 <= len(result.strip()) <= 80:
            logger.info(f"[GroqGuard] Titre généré : {result.strip()!r}")
            return result.strip()
        return None


# Singleton partagé importé par chat.py
groq_guard = GroqGuard()
