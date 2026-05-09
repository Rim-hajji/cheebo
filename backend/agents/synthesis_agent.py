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
from typing import Any, Dict

from backend.agents.base_llm_agent import BaseLLMAgent


SYSTEM_PROMPT = """Tu es Cheebo, l'assistant vétérinaire intelligent de la plateforme Cheebo.

Tu reçois l'analyse complète d'un pipeline multi-agents IA : symptômes normalisés,
niveau d'urgence raffiné par LLM, diagnostic différentiel, plan de soin personnalisé,
informations d'urgence, et conseils issus de cas similaires (RAG).

Ton rôle est de synthétiser tout cela en UNE SEULE réponse conversationnelle,
intelligente, empathique et parfaitement adaptée à la situation.

RÈGLES OBLIGATOIRES :
1. Réponds TOUJOURS dans la langue indiquée par le champ "language" (fr / en / ar)
2. Intègre les informations naturellement — NE LES LISTE PAS mécaniquement
3. Adapte le ton selon l'urgence :
   - CRITICAL / HIGH  → direct, urgent, chaque seconde compte, vétérinaire immédiat
   - MODERATE         → attentif, étapes concrètes, consulter sous 24-48h
   - LOW              → rassurant, informatif, surveillance à domicile
4. Cite l'animal par son espèce si disponible ("votre chat", "your dog", "كلبك")
5. Mentionne les conditions possibles du diagnostic différentiel (sans les présenter comme certaines)
6. Intègre les actions concrètes du plan de soin dans le texte naturellement
7. Si emergency=true, mentionne les vétérinaires disponibles avec leur numéro
8. Tu N'ES PAS un vétérinaire — ne pose jamais de diagnostic définitif
9. Termine par une note de réassurance appropriée au niveau d'urgence

FORMAT DE RÉPONSE — JSON pur, sans markdown autour :
{
  "response_text": "réponse complète en Markdown conversationnel (utilise **gras**, •, _italique_)",
  "urgency_summary": "une phrase courte résumant l'urgence pour l'interface"
}"""


class SynthesisAgent(BaseLLMAgent):
    """
    Agent de synthèse finale.
    Reçoit la réponse agrégée de tous les agents et génère
    un texte conversationnel intelligent dans la langue de l'utilisateur.
    """
    name          = "SynthesisAgent"
    system_prompt = SYSTEM_PROMPT
    tools         = []  # Pas d'outils — synthèse pure

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
            "partner_vets"        : [
                {"name": v.get("name", ""), "phone": v.get("phone", "")}
                for v in emergency.get("partner_vets", [])[:2]
            ],
            "rag_advice"          : rag.get("advice") if rag.get("confidence", 0) > 0.5 else None,
            "rag_home_care"       : rag.get("home_care", [])[:2] if rag.get("confidence", 0) > 0.6 else [],
            "gemini_message"      : rec.get("message", ""),
            "gemini_actions"      : rec.get("actions", []),
            "gemini_warnings"     : rec.get("warnings", []),
            "gemini_next_steps"   : rec.get("next_steps", ""),
            "should_consult"      : rec.get("should_consult", True),
        }

        return (
            f"Analyse complète du pipeline DoctoAgent pour une réponse en '{language}' :\n\n"
            + json.dumps(synthesis_input, ensure_ascii=False, indent=2)
            + "\n\nGénère une réponse conversationnelle intelligente. JSON uniquement."
        )

    def _parse_output(self, raw: str, context: Dict[str, Any]) -> Dict[str, Any]:
        parsed = self._extract_json(raw)
        if parsed and "response_text" in parsed:
            return parsed
        # Si Gemini répond en texte libre sans JSON → l'utiliser directement
        if isinstance(raw, str) and len(raw.strip()) > 30:
            return {
                "response_text"  : raw.strip(),
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
