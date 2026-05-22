"""
DoctoAgent — Recommendation Agent (LLM-powered)
================================================
Agent unifié qui remplace CareAgent + EmergencyAgent + l'ancien RecommendationAgent.

Rôle : produire la réponse finale complète adaptée au niveau d'urgence :
  - LOW/MODERATE : plan de soin à domicile + message rassurant
  - HIGH          : alerte urgence + plan de soin + vétérinaires disponibles
  - CRITICAL      : alerte critique + actions immédiates + vétérinaires d'urgence

L'agent choisit lui-même quels outils utiliser selon la situation.

Auteur : Rim Hajji — PFE 2026
"""

import json
from typing import Any, Dict

from backend.agents.base_llm_agent import BaseLLMAgent
from backend.agents.tools import RESPONSE_TOOLS

SAFETY_WARNING = (
    "⚕️ IMPORTANT : DoctoAgent est un outil d'aide à la décision et ne remplace "
    "en aucun cas l'avis d'un vétérinaire professionnel. En cas de doute, "
    "consultez toujours un vétérinaire."
)

SYSTEM_PROMPT = """Agent de recommandation DoctoAgent/Cheebo. Conseils préventifs uniquement — jamais de diagnostic ferme.

LOW/MODERATE → utilise KB_CONTEXT, ⛔ aucun outil.
HIGH → find_partner_vets(emergency_only=False) + actions immédiates.
CRITICAL → find_partner_vets(emergency_only=True) + get_first_aid_steps() si pertinent.
Diet : vomissements/diarrhée → diète 12h puis riz+poulet. HIGH/CRITICAL → rien sans avis vétérinaire.

JSON uniquement :
{"is_emergency":false,"urgency_level":"","alert_message":null,"immediate_actions":[],"partner_vets":[],"should_redirect":false,"care_plan":{"immediate_actions":[],"home_care_steps":[],"monitoring_signs":[],"when_to_consult":"","diet_advice":null,"timeline":[],"symptoms_covered":[]},"care_summary":"","kb_symptoms_found":[],"message":"","actions":[],"warnings":[],"next_steps":"","should_consult":true,"severity":"","safety_warning":"","confidence":0.0}"""


class RecommendationAgent(BaseLLMAgent):
    name          = "RecommendationAgent"
    system_prompt = SYSTEM_PROMPT
    tools         = RESPONSE_TOOLS

    def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Pour LOW/MODERATE : désactive les outils (KB suffit, évite les appels inutiles)."""
        urgency = (
            context.get("_urgency_context", {}).get("refined_level")
            or context.get("urgency_label", "LOW")
        )
        if urgency in ("LOW", "MODERATE"):
            saved_llm_with_tools = self.llm_with_tools
            saved_tools_map      = self.tools_map
            self.llm_with_tools  = self.llm
            self.tools_map       = {}
            result = super().run(context)
            self.llm_with_tools  = saved_llm_with_tools
            self.tools_map       = saved_tools_map
            return result
        return super().run(context)

    def _build_prompt(self, context: Dict[str, Any]) -> str:
        symptom_ctx   = context.get("_symptom_context", {})
        urgency_ctx   = context.get("_urgency_context", {})
        kb_context    = context.get("_kb_context", {})
        prediction    = context.get("_prediction_context", {})
        urgency_level = urgency_ctx.get("refined_level", context.get("urgency_label", "LOW"))
        normalized    = symptom_ctx.get("symptoms_normalized", [])

        # Extraire uniquement les champs utiles du KB (home_care, red_flags, timeline)
        # _collected stocke les retours d'outils en strings JSON → parser avant slicing
        def _kb_list(val, n):
            if isinstance(val, list):
                return val[:n]
            if isinstance(val, str) and not val.startswith(("Aucun", "Pas d", "Symptôme")):
                try:
                    parsed = json.loads(val)
                    return parsed[:n] if isinstance(parsed, list) else []
                except Exception:
                    pass
            return []

        def _kb_dict(val):
            if isinstance(val, dict):
                return val
            if isinstance(val, str):
                try:
                    parsed = json.loads(val)
                    return parsed if isinstance(parsed, dict) else {}
                except Exception:
                    pass
            return {}

        kb_slim = {}
        for sym in normalized:
            d = kb_context.get("symptoms_data", {}).get(sym, {})
            if d:
                home_care = _kb_list(d.get("home_care", []), 4)
                red_flags = _kb_list(d.get("red_flags", []), 3)
                timeline  = _kb_dict(d.get("timeline", {}))
                if home_care or red_flags:
                    kb_slim[sym] = {
                        "home_care": home_care,
                        "red_flags": red_flags,
                        "timeline" : timeline,
                    }

        assoc_slim = [
            {"condition": a.get("condition"), "urgency_hint": a.get("urgency_hint")}
            for a in prediction.get("possible_associations", [])[:2]
            if isinstance(a, dict)
        ]

        return (
            f"Texte:«{context.get('original_text','')}»\n"
            f"Animal:{symptom_ctx.get('animal','?')} | "
            f"Symptômes:{normalized} | "
            f"Durée:{symptom_ctx.get('duration','?')} | "
            f"Urgence:{urgency_level} | "
            f"RedFlags:{urgency_ctx.get('red_flags_found',[])}\n"
            f"Associations:{json.dumps(assoc_slim, ensure_ascii=False, separators=(',',':'))}\n"
            f"KB:{json.dumps(kb_slim, ensure_ascii=False, separators=(',',':'))}\n"
            f"Retourne le JSON complet."
        )

    # Correspondance symptôme → clé KB (pour le fallback)
    _SYMPTOM_KB_MAP = {
        "vomit": "vomissement", "vomissement": "vomissement", "vomiting": "vomissement",
        "diarrhée": "diarrhée", "diarrhea": "diarrhée",
        "toux": "toux", "cough": "toux",
        "convulsion": "convulsion", "seizure": "convulsion",
        "boiterie": "boiterie", "limp": "boiterie",
        "apathie": "apathie", "léthargie": "apathie", "lethargy": "apathie",
        "démangeaison": "démangeaison", "itching": "démangeaison",
        "fièvre": "fièvre", "fever": "fièvre",
        "intoxication": "intoxication", "poison": "intoxication",
        "choc": "choc", "shock": "choc", "collapse": "choc",
    }

    def _kb_care_data(self, symptoms: list) -> tuple:
        from backend.agents.tools import _KB
        steps, red_flags, timeline, covered = [], [], [], []
        seen = set()
        for sym in symptoms:
            kb_key = self._SYMPTOM_KB_MAP.get(sym.lower())
            if not kb_key or kb_key in seen:
                continue
            entry = _KB.get(kb_key, {})
            if not entry:
                continue
            seen.add(kb_key)
            covered.append(kb_key)
            steps.extend(entry.get("conseils_maison", []))
            red_flags.extend(entry.get("red_flags", []))
            evo = entry.get("evolution_attendue", {})
            for tf, desc in list(evo.items())[:1]:
                timeline.append({"timeframe": tf.replace("_", " "), "description": desc})
        return steps, red_flags, timeline, covered

    def _parse_output(self, raw: str, context: Dict[str, Any]) -> Dict[str, Any]:
        parsed = self._extract_json(raw)
        if parsed:
            if "safety_warning" not in parsed:
                parsed["safety_warning"] = SAFETY_WARNING
            return parsed
        return self._fallback(context, error="JSON parse failed")

    def _fallback(self, context: Dict[str, Any], error: str = "") -> Dict[str, Any]:
        urgency  = context.get("_urgency_context", {}).get(
            "refined_level", context.get("urgency_label", "LOW")
        )
        symptoms = context.get("_symptom_context", {}).get("symptoms_normalized", [])
        kb_steps, kb_flags, kb_timeline, covered = self._kb_care_data(symptoms)

        is_emergency = urgency in ("HIGH", "CRITICAL")

        immediate_map = {
            "LOW"     : [],
            "MODERATE": ["Surveiller attentivement l'animal", "Limiter l'activité physique"],
            "HIGH"    : ["Garder l'animal au calme", "Préparer le transport chez le vétérinaire"],
            "CRITICAL": ["Ne rien donner par voie orale", "Urgences vétérinaires immédiatement"],
        }
        home_care_map = {
            "LOW"     : ["Assurez-vous que l'animal a accès à de l'eau fraîche",
                         "Laissez-le se reposer dans un endroit calme"],
            "MODERATE": ["Proposez de petites quantités d'eau régulièrement",
                         "Alimentation légère : riz blanc + poulet bouilli sans sel"],
            "HIGH"    : ["Gardez l'animal au chaud et au calme",
                         "Aucun médicament sans avis vétérinaire"],
            "CRITICAL": ["Ne rien administrer par voie orale",
                         "Gardez l'animal immobile et au chaud"],
        }
        when_map = {
            "LOW"     : "Si les symptômes persistent plus de 48h ou s'aggravent",
            "MODERATE": "Dans les 24 à 48 heures",
            "HIGH"    : "Dans les prochaines heures — ne pas attendre",
            "CRITICAL": "Immédiatement — urgence vétérinaire",
        }
        message_map = {
            "LOW"     : "Les symptômes décrits semblent bénins. Une surveillance à domicile peut suffire.",
            "MODERATE": "Les symptômes nécessitent une surveillance attentive. Une consultation est conseillée dans les 24-48 heures.",
            "HIGH"    : "Les symptômes décrits sont préoccupants. Consultez un vétérinaire dans les prochaines heures.",
            "CRITICAL": "Cette situation semble critique. Consultez immédiatement un vétérinaire d'urgence.",
        }

        diet = None
        syms_lower = [s.lower() for s in symptoms]
        if any(s in syms_lower for s in ["vomissement", "diarrhée", "anorexie"]):
            diet = ("Ne rien donner sans avis vétérinaire" if is_emergency
                    else "Diète stricte 12h puis alimentation légère : riz blanc + poulet bouilli sans sel")

        care_steps = kb_steps[:4] if kb_steps else home_care_map.get(urgency, [])
        monitoring = kb_flags[:3] if kb_flags else {
            "LOW"     : ["Perte d'appétit persistante", "Léthargie inhabituelle"],
            "MODERATE": ["Vomissements répétés", "Refus de boire"],
            "HIGH"    : ["Difficultés respiratoires", "Perte de conscience"],
            "CRITICAL": ["Arrêt respiratoire", "Perte de conscience totale"],
        }.get(urgency, [])

        return {
            "is_emergency"    : is_emergency,
            "urgency_level"   : urgency,
            "alert_message"   : (
                "Situation urgente détectée. Consultez un vétérinaire rapidement."
                if is_emergency else None
            ),
            "immediate_actions": immediate_map.get(urgency, []),
            "partner_vets"    : [],
            "should_redirect" : is_emergency,
            "care_plan"       : {
                "immediate_actions": immediate_map.get(urgency, []),
                "home_care_steps"  : care_steps,
                "monitoring_signs" : monitoring,
                "when_to_consult"  : when_map.get(urgency, when_map["LOW"]),
                "diet_advice"      : diet,
                "timeline"         : kb_timeline,
                "symptoms_covered" : covered,
            },
            "care_summary"    : (
                f"Plan de soin basé sur KB pour : {', '.join(covered)}."
                if covered else "Conseils généraux adaptés au niveau d'urgence."
            ),
            "kb_symptoms_found": covered,
            "message"         : message_map.get(urgency, message_map["LOW"]),
            "actions"         : care_steps[:3] if care_steps else ["Surveiller l'animal", "Maintenir l'hydratation"],
            "warnings"        : monitoring[:2],
            "next_steps"      : when_map.get(urgency, when_map["LOW"]),
            "should_consult"  : urgency != "LOW",
            "severity"        : urgency,
            "safety_warning"  : SAFETY_WARNING,
            "confidence"      : 0.5 if covered else 0.2,
            "status"          : "fallback",
        }
