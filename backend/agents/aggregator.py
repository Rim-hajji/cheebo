"""
DoctoAgent — Aggregator
========================
Fusionne les résultats de tous les agents LLM en une réponse finale
structurée, cohérente et prête à être renvoyée par l'API.

Responsabilités :
  - Assembler les sorties (plain dicts) de chaque agent en un objet JSON
  - Résoudre les conflits d'urgence (choisir le niveau le plus sévère)
  - Construire le message principal de la réponse
  - Injecter le disclaimer de sécurité obligatoire
  - Calculer les méta-données du pipeline (temps, agents utilisés, version)

Auteur : Rim Hajji — PFE 2026
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

PIPELINE_VERSION = "2.0.0"

SAFETY_DISCLAIMER = (
    "⚕️ DoctoAgent est un outil d'aide à la décision. "
    "Ses recommandations ne constituent pas un diagnostic médical "
    "et ne remplacent en aucun cas l'avis d'un vétérinaire professionnel. "
    "En cas de doute, consultez toujours un vétérinaire."
)

_URGENCY_RANK = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}


def _higher_urgency(a: str, b: str) -> str:
    return a if _URGENCY_RANK.get(a, 0) >= _URGENCY_RANK.get(b, 0) else b


class Aggregator:
    """
    Fusionne les résultats (plain dicts) de tous les agents LLM
    en une réponse finale structurée.
    """

    def aggregate_from_dicts(
        self,
        nlp_dict              : Dict[str, Any],
        symptom_ctx           : Dict[str, Any],
        urgency_ctx           : Dict[str, Any],
        prediction_ctx        : Dict[str, Any],
        validation_ctx        : Dict[str, Any],
        emergency_ctx         : Dict[str, Any],
        care_ctx              : Dict[str, Any],
        rag_ctx               : Dict[str, Any],
        recommendation_ctx    : Dict[str, Any],
        agent_timings         : Optional[Dict[str, float]] = None,
    ) -> Dict[str, Any]:
        agent_timings = agent_timings or {}

        analysis       = self._build_analysis(nlp_dict, urgency_ctx)
        symptoms       = self._build_symptoms(symptom_ctx)
        predictions    = self._build_predictions(prediction_ctx)
        validation     = self._build_validation(validation_ctx)
        urgency        = self._build_urgency(urgency_ctx, nlp_dict)
        emergency      = self._build_emergency(emergency_ctx)
        care_plan      = self._build_care(care_ctx)
        rag_advice     = self._build_rag(rag_ctx)
        recommendation = self._build_recommendation(recommendation_ctx)
        main_message   = self._build_main_message(
            emergency_ctx, recommendation_ctx, urgency_ctx, nlp_dict
        )
        metadata = self._build_metadata(nlp_dict, agent_timings)

        return {
            "status"           : "success",
            "main_message"     : main_message,
            "analysis"         : analysis,
            "urgency"          : urgency,
            "symptoms"         : symptoms,
            "predictions"      : predictions,
            "validation"       : validation,
            "emergency"        : emergency,
            "care_plan"        : care_plan,
            "rag_advice"       : rag_advice,
            "recommendation"   : recommendation,
            "safety_disclaimer": SAFETY_DISCLAIMER,
            "metadata"         : metadata,
        }

    # ─────────────────────────────────────────
    # Blocs de construction
    # ─────────────────────────────────────────

    def _build_analysis(self, nlp: Dict, urgency_ctx: Dict) -> Dict:
        return {
            "original_text"    : nlp.get("original_text", ""),
            "language"         : nlp.get("language", "en"),
            "intent"           : nlp.get("intent", ""),
            "intent_confidence": round(nlp.get("intent_confidence", 0.0), 3),
            "entities"         : nlp.get("entities", []),
            "ner_source"       : nlp.get("ner_source", ""),
        }

    def _build_urgency(self, urgency_ctx: Dict, nlp: Dict) -> Dict:
        nlp_level = urgency_ctx.get("nlp_level", nlp.get("urgency_label", "LOW"))
        refined   = urgency_ctx.get("refined_level", nlp_level)
        return {
            "level"             : refined,
            "score"             : urgency_ctx.get("refined_score",
                                    nlp.get("urgency_score", 1)),
            "label"             : urgency_ctx.get("label", refined),
            "confidence"        : urgency_ctx.get("confidence", 0.0),
            "nlp_level"         : nlp_level,
            "was_escalated"     : urgency_ctx.get("was_escalated", False),
            "was_downgraded"    : urgency_ctx.get("was_downgraded", False),
            "escalation_triggers": urgency_ctx.get("escalation_triggers", []),
            "red_flags_found"   : urgency_ctx.get("red_flags_found", []),
            "reasoning"         : urgency_ctx.get("reasoning_steps", []),
        }

    def _build_symptoms(self, ctx: Dict) -> Dict:
        return {
            "animal"              : ctx.get("animal", "inconnu"),
            "animal_raw"          : ctx.get("animal_raw", ""),
            "symptoms_detected"   : ctx.get("symptoms_raw", []),
            "symptoms_normalized" : ctx.get("symptoms_normalized", []),
            "duration"            : ctx.get("duration"),
            "severity_indicators" : ctx.get("severity_indicators", []),
            "has_severity_flag"   : ctx.get("has_severity_flag", False),
            "symptom_count"       : ctx.get("symptom_count", 0),
            "confidence"          : ctx.get("confidence", 0.0),
        }

    def _build_predictions(self, ctx: Dict) -> Dict:
        raw = ctx.get("possible_associations", [])
        associations = [
            {
                "condition"      : c.get("condition", ""),
                "frequency"      : c.get("frequency", "LOW"),
                "source_symptoms": c.get("source_symptoms", []),
                "requires_vet"   : c.get("requires_vet", False),
                "urgency_hint"   : c.get("urgency_hint", "LOW"),
                "watch_for"      : c.get("watch_for", ""),
            }
            for c in raw
            if isinstance(c, dict)
        ]
        return {
            "possible_associations"  : associations,
            "main_concern"           : ctx.get("main_concern"),
            "watch_delay"            : ctx.get("watch_delay", "48h"),
            "symptoms_analyzed"      : ctx.get("symptoms_analyzed", []),
            "kb_coverage"            : ctx.get("kb_coverage", 0.0),
            "vet_consultation_needed": ctx.get("vet_consultation_needed", True),
            "confidence"             : ctx.get("confidence", 0.0),
            "orientation_summary"    : ctx.get("orientation_summary", ""),
            "disclaimer"             : (
                "Ces pistes sont indicatives et ne constituent pas un diagnostic médical. "
                "Seul un vétérinaire peut poser un diagnostic après examen clinique."
            ),
        }

    def _build_validation(self, ctx: Dict) -> Dict:
        raw_issues = ctx.get("issues", [])
        issues = [
            {
                "check_id"   : i.get("check_id", ""),
                "severity"   : i.get("severity", "WARNING"),
                "description": i.get("description", ""),
                "suggestion" : i.get("suggestion"),
            }
            for i in raw_issues
            if isinstance(i, dict)
        ]
        return {
            "is_valid"          : ctx.get("is_valid", True),
            "overall_quality"   : ctx.get("overall_quality", "ACCEPTABLE"),
            "pipeline_score"    : ctx.get("pipeline_score", 0.5),
            "checks_passed"     : ctx.get("checks_passed", 0),
            "checks_total"      : ctx.get("checks_total", 5),
            "issues"            : issues,
            "corrections"       : ctx.get("corrections", []),
            "validation_summary": ctx.get("validation_summary", ""),
        }

    def _build_emergency(self, ctx: Dict) -> Dict:
        if not ctx.get("is_emergency", False):
            return {"is_emergency": False}

        raw_vets = ctx.get("partner_vets", [])
        vets = [
            {
                "id"         : v.get("id", ""),
                "name"       : v.get("name", ""),
                "phone"      : v.get("phone", ""),
                "address"    : v.get("address", ""),
                "specialties": v.get("specialties", []),
                "emergency"  : v.get("emergency", False),
            }
            for v in raw_vets
            if isinstance(v, dict)
        ]
        return {
            "is_emergency"     : True,
            "urgency_level"    : ctx.get("urgency_level", "HIGH"),
            "alert_message"    : ctx.get("alert_message"),
            "immediate_actions": ctx.get("immediate_actions", []),
            "should_redirect"  : ctx.get("should_redirect", True),
            "partner_vets"     : vets,
            "safety_warning"   : ctx.get("safety_warning", ""),
        }

    def _build_care(self, ctx: Dict) -> Dict:
        plan = ctx.get("care_plan", {})
        if not plan:
            return {}

        raw_timeline = plan.get("timeline", [])
        timeline = [
            {"timeframe": t.get("timeframe", ""), "description": t.get("description", "")}
            for t in raw_timeline
            if isinstance(t, dict)
        ]
        return {
            "urgency_level"    : ctx.get("urgency_level", "LOW"),
            "immediate_actions": plan.get("immediate_actions", []),
            "home_care_steps"  : plan.get("home_care_steps", []),
            "monitoring_signs" : plan.get("monitoring_signs", []),
            "when_to_consult"  : plan.get("when_to_consult", ""),
            "diet_advice"      : plan.get("diet_advice"),
            "timeline"         : timeline,
            "symptoms_covered" : plan.get("symptoms_covered", []),
            "care_summary"     : ctx.get("care_summary", ""),
            "confidence"       : ctx.get("confidence", 0.0),
        }

    def _build_rag(self, ctx: Dict) -> Dict:
        if not ctx:
            return {}
        return {
            "scenario_id"    : ctx.get("scenario_id"),
            "title"          : ctx.get("title"),
            "advice"         : ctx.get("advice"),
            "home_care"      : ctx.get("home_care", []),
            "watch_for"      : ctx.get("watch_for", []),
            "when_to_consult": ctx.get("when_to_consult"),
            "urgency"        : ctx.get("urgency"),
            "confidence"     : round(ctx.get("confidence", 0.0), 3),
            "match_quality"  : ctx.get("match_quality"),
            "is_fallback"    : ctx.get("is_fallback", True),
        }

    def _build_recommendation(self, ctx: Dict) -> Dict:
        if not ctx:
            return {}
        return {
            "message"       : ctx.get("message", ""),
            "actions"       : ctx.get("actions", []),
            "warnings"      : ctx.get("warnings", []),
            "next_steps"    : ctx.get("next_steps", []),
            "severity"      : ctx.get("severity"),
            "should_consult": ctx.get("should_consult", False),
        }

    def _build_main_message(
        self,
        emergency_ctx    : Dict,
        recommendation_ctx: Dict,
        urgency_ctx      : Dict,
        nlp_dict         : Dict,
    ) -> str:
        if emergency_ctx.get("is_emergency") and emergency_ctx.get("alert_message"):
            return emergency_ctx["alert_message"]

        msg = recommendation_ctx.get("message", "")
        if msg:
            return msg

        level = urgency_ctx.get("refined_level",
                nlp_dict.get("urgency_label", "LOW"))
        fallbacks = {
            "CRITICAL": "Situation critique détectée. Rendez-vous immédiatement chez un vétérinaire.",
            "HIGH"    : "Symptômes préoccupants. Consultez un vétérinaire rapidement.",
            "MODERATE": "Surveillance recommandée. Prenez rendez-vous chez votre vétérinaire.",
            "LOW"     : "Symptômes bénins détectés. Surveillez votre animal à domicile.",
        }
        return fallbacks.get(level, fallbacks["LOW"])

    def _build_metadata(
        self,
        nlp_dict     : Dict,
        agent_timings: Dict[str, float],
    ) -> Dict:
        total_time  = sum(agent_timings.values())
        agents_used = list(agent_timings.keys())
        return {
            "pipeline_version"   : PIPELINE_VERSION,
            "timestamp"          : datetime.now(timezone.utc).isoformat(),
            "agents_used"        : agents_used,
            "agent_timings_ms"   : agent_timings,
            "total_processing_ms": round(total_time, 2),
            "language"           : nlp_dict.get("language", "en"),
        }
