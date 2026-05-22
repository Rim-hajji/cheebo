"""
DoctoAgent — Synthesis Agent
==============================
Agent LLM final : synthétise tous les résultats du pipeline en une
réponse conversationnelle unique, intelligente et empathique.

Remplace la fonction _build_chat_response() (templates statiques) par une
génération Gemini qui reçoit l'analyse complète (urgency, symptoms,
predictions, care_plan, emergency, rag, recommendation) et produit un
texte naturel et personnalisé dans la langue de l'utilisateur.

Auteur : Rim Hajji — PFE 2026
"""

import json
import logging
from typing import Any, Dict

from backend.agents.base_llm_agent import BaseLLMAgent, _get_cheebo_singleton, CHEEBO_MODEL_PATH
import os

logger = logging.getLogger("doctoagent.synthesis_agent")


SYSTEM_PROMPT = """Tu es Cheebo, assistant vétérinaire IA de la plateforme Cheebo.

Synthétise l'analyse pipeline en UNE réponse conversationnelle empathique dans la langue du champ "language".
Ton : CRITICAL/HIGH=urgent et préoccupé | MODERATE=attentif | LOW=rassurant.
Cite l'espèce, mentionne les conditions POSSIBLES sans les affirmer, intègre les soins naturellement.

INTERDITS ABSOLUS — violation = réponse rejetée :
1. Jamais de diagnostic définitif ("c'est X", "votre animal a X") — uniquement des pistes possibles.
2. Jamais de numéro de téléphone, nom de clinique ou de vétérinaire dans le texte.
   Les vétérinaires partenaires Cheebo sont affichés séparément en cartes cliquables vérifiées.
3. Jamais "je suis heureux/ravi/content" face à des symptômes — empathie uniquement.
4. Jamais de JSON, d'accolades {{ }}, de balises ou de formatage technique dans la réponse.

Réponds en TEXTE DIRECT avec Markdown (**, •, _italique_). Rien d'autre."""


class SynthesisAgent(BaseLLMAgent):
    """
    Agent de synthèse finale.
    Reçoit la réponse agrégée de tous les agents et génère
    un texte conversationnel intelligent dans la langue de l'utilisateur.
    """
    name          = "SynthesisAgent"
    system_prompt = SYSTEM_PROMPT
    tools         = []

    def __init__(self):
        super().__init__()
        # Force Cheebo pour la synthèse finale si le modèle est disponible
        if os.path.exists(CHEEBO_MODEL_PATH):
            try:
                self.llm = _get_cheebo_singleton()
                self.llm_with_tools = self.llm
                logger.info("[SynthesisAgent] Cheebo forcé pour la synthèse finale")
            except Exception as e:
                logger.warning(f"[SynthesisAgent] Cheebo indisponible, fallback provider actuel : {e}")

    def _build_prompt(self, context: Dict[str, Any]) -> str:
        urgency     = context.get("urgency", {})
        symptoms    = context.get("symptoms", {})
        predictions = context.get("predictions", {})
        care        = context.get("care_plan", {})
        emergency   = context.get("emergency", {})
        rag         = context.get("rag_advice", {})
        analysis    = context.get("analysis", {})
        rec         = context.get("recommendation", {})

        language = analysis.get("language", "en")

        synthesis_input = {
            "language"            : language,
            "original_message"    : analysis.get("original_text", ""),
            "animal"              : symptoms.get("animal", ""),
            "urgency_level"       : urgency.get("level", "LOW"),
            "red_flags_found"     : urgency.get("red_flags_found", []),
            "urgency_reasoning"   : urgency.get("reasoning", [])[:2],
            "was_escalated"       : urgency.get("was_escalated", False),
            "symptoms_detected"   : symptoms.get("symptoms_detected", []),
            "symptoms_normalized" : symptoms.get("symptoms_normalized", []),
            "duration"            : symptoms.get("duration"),
            "possible_conditions" : [
                {
                    "condition" : p.get("condition", ""),
                    "frequency" : p.get("frequency", ""),
                    "watch_for" : p.get("watch_for", ""),
                    "requires_vet": p.get("requires_vet", False),
                }
                for p in predictions.get("possible_associations", [])[:3]
                if isinstance(p, dict)
            ],
            "home_care_steps"     : care.get("home_care_steps", [])[:4],
            "diet_advice"         : care.get("diet_advice"),
            "when_to_consult"     : care.get("when_to_consult", ""),
            "monitoring_signs"    : care.get("monitoring_signs", [])[:3],
            "care_summary"        : care.get("care_summary", ""),
            "is_emergency"        : emergency.get("is_emergency", False),
            "immediate_actions"   : emergency.get("immediate_actions", [])[:4],
            # partner_vets intentionnellement absent — affichés en cartes séparées côté frontend
            "rag_advice"          : rag.get("advice") if rag.get("confidence", 0) > 0.5 else None,
            "rag_home_care"       : rag.get("home_care", [])[:2] if rag.get("confidence", 0) > 0.6 else [],
            "gemini_message"      : rec.get("message", ""),
            "gemini_actions"      : rec.get("actions", []),
            "gemini_warnings"     : rec.get("warnings", []),
            "gemini_next_steps"   : rec.get("next_steps", ""),
            "should_consult"      : rec.get("should_consult", True),
        }

        return (
            f"Langue:'{language}'. Données du pipeline:\n"
            + json.dumps(synthesis_input, ensure_ascii=False, separators=(',', ':'))
            + "\nTexte direct uniquement — pas de JSON."
        )

    def _parse_output(self, raw: str, context: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(raw, str) or not raw.strip():
            return self._fallback(context)

        text = raw.strip()

        # Cas où le LLM ignore la consigne et retourne quand même du JSON
        if text.startswith("{"):
            try:
                obj = json.loads(text)
                if isinstance(obj, dict):
                    for key in ("response_text", "responsetext", "response", "text", "content"):
                        val = obj.get(key) or obj.get(key.upper())
                        if isinstance(val, str) and len(val) > 30:
                            text = val
                            break
            except Exception:
                # JSON mal formé — extraire tout ce qui suit la première ":" string
                import re
                m = re.search(r'["\'](response[^"\']*|text|content)["\']\s*:\s*["\'](.+?)(?:["\'](?:\s*[,}]|$))', text, re.DOTALL | re.IGNORECASE)
                if m:
                    text = m.group(2)

        if len(text) > 30:
            return {
                "response_text"  : text,
                "urgency_summary": "",
            }
        return self._fallback(context)

    def _fallback(self, context: Dict[str, Any], error: str = "") -> Dict[str, Any]:
        """Fallback : retourne le message du RecommendationAgent si disponible."""
        rec   = context.get("recommendation", {})
        level = context.get("urgency", {}).get("level", "LOW")
        msg   = rec.get("message", "")
        if not msg:
            fallbacks = {
                "CRITICAL": "Situation critique — rendez-vous immédiatement aux urgences vétérinaires.",
                "HIGH"    : "Symptômes préoccupants — consultez un vétérinaire dans les heures qui viennent.",
                "MODERATE": "Surveillance recommandée — prenez rendez-vous sous 24-48h.",
                "LOW"     : "Symptômes bénins — surveillance à domicile conseillée.",
            }
            msg = fallbacks.get(level, fallbacks["LOW"])
        return {
            "response_text"  : msg,
            "urgency_summary": level,
            "status"         : "fallback",
            "error"          : error,
        }
