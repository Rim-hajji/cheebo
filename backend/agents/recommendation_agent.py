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

SYSTEM_PROMPT = """Tu es un assistant vétérinaire expert pour DoctoAgent/Cheebo.

TON RÔLE :
Produire la réponse finale complète pour le propriétaire, adaptée au niveau d'urgence.
Tu combines : plan de soin, alerte urgence (si nécessaire), et message de recommandation.

RÈGLE ABSOLUE :
DoctoAgent ne pose PAS de diagnostic. Utilise toujours :
✅ "Ces symptômes sont fréquemment associés à..."
✅ "Consultez un vétérinaire si..."
❌ Jamais : "Votre animal a [maladie]" ou "Le diagnostic est..."

ADAPTATION SELON L'URGENCE :
- LOW      : message rassurant, conseils depuis KB_CONTEXT. ⛔ AUCUN outil à appeler.
- MODERATE : surveillance active, conseils KB_CONTEXT, préparer la consultation. ⛔ AUCUN outil à appeler.
- HIGH     : appelle find_partner_vets(emergency_only=False) + actions immédiates.
- CRITICAL : appelle find_partner_vets(emergency_only=True) + get_first_aid_steps() si intoxication/convulsion/choc.

⛔ RÈGLE STRICTE : si urgence_level = LOW ou MODERATE → N'appelle AUCUN outil. Utilise UNIQUEMENT KB_CONTEXT.
✅ RÈGLE : si urgence_level = HIGH ou CRITICAL → appelle les outils d'urgence ci-dessous.

OUTILS (HIGH/CRITICAL uniquement) :
- find_partner_vets(emergency_only)     : vétérinaires partenaires Cheebo
- get_first_aid_steps(emergency_type)   : intoxication, convulsion, coup_de_chaleur, hemorragie, choc, fracture
- get_toxic_foods(species)              : si intoxication alimentaire suspectée
- web_search_vet(query)                 : si substance toxique spécifique non documentée

CONSEILS ALIMENTAIRES :
- Vomissements/diarrhée : diète 12h puis riz blanc + poulet bouilli sans sel
- HIGH/CRITICAL         : ne rien donner sans avis vétérinaire

IMPORTANT : Réponds UNIQUEMENT avec un objet JSON valide :
{
  "is_emergency"    : true/false,
  "urgency_level"   : "LOW | MODERATE | HIGH | CRITICAL",
  "alert_message"   : "message d'alerte urgent ou null si LOW/MODERATE",
  "immediate_actions": ["action urgente 1", ...],
  "partner_vets"    : [{"id":"...","name":"...","phone":"...","address":"...","specialties":[...],"emergency":true}],
  "should_redirect" : true/false,
  "care_plan"       : {
    "immediate_actions": ["action prioritaire 1", ...],
    "home_care_steps"  : ["conseil pratique 1", ...],
    "monitoring_signs" : ["signe à surveiller 1", ...],
    "when_to_consult"  : "quand consulter un vétérinaire",
    "diet_advice"      : "conseil alimentaire ou null",
    "timeline"         : [{"timeframe": "24h", "description": "ce qui peut se passer"}],
    "symptoms_covered" : ["symptôme1", ...]
  },
  "care_summary"    : "résumé du plan de soin en 1-2 phrases",
  "kb_symptoms_found": ["symptômes trouvés dans KB"],
  "message"         : "message empathique principal pour le propriétaire (2-3 phrases)",
  "actions"         : ["action concrète 1", "action 2", ...],
  "warnings"        : ["avertissement 1", ...],
  "next_steps"      : "prochaines étapes concrètes",
  "should_consult"  : true/false,
  "severity"        : "LOW | MODERATE | HIGH | CRITICAL",
  "safety_warning"  : "avertissement de sécurité standard",
  "confidence"      : 0.0-1.0
}"""


class RecommendationAgent(BaseLLMAgent):
    name          = "RecommendationAgent"
    system_prompt = SYSTEM_PROMPT
    tools         = RESPONSE_TOOLS

    def _build_prompt(self, context: Dict[str, Any]) -> str:
        symptom_ctx   = context.get("_symptom_context", {})
        urgency_ctx   = context.get("_urgency_context", {})
        kb_context    = context.get("_kb_context", {})
        prediction    = context.get("_prediction_context", {})
        urgency_level = urgency_ctx.get("refined_level", context.get("urgency_label", "LOW"))

        return f"""Génère la réponse finale pour la situation suivante :

TEXTE ORIGINAL : "{context.get("original_text", "")}"
INTENTION NLP  : {context.get("intent", "")}

PATIENT :
- Animal     : {symptom_ctx.get("animal", "inconnu")}
- Symptômes  : {symptom_ctx.get("symptoms_normalized", [])}
- Durée      : {symptom_ctx.get("duration", "non précisée")}
- Urgence    : {urgency_level}
- Red flags  : {urgency_ctx.get("red_flags_found", [])}

ORIENTATION (PredictionAgent) :
- Préoccupation principale : {prediction.get("main_concern", "non disponible")}
- Délai surveillance       : {prediction.get("watch_delay", "48h")}
- Associations             : {json.dumps(prediction.get("possible_associations", [])[:2], ensure_ascii=False)}

KB_CONTEXT (home_care, timeline, red_flags pré-chargés) :
{json.dumps(kb_context, ensure_ascii=False, indent=2)}

INSTRUCTIONS :
- Si urgence LOW/MODERATE : utilise KB_CONTEXT directement, aucun outil
- Si urgence HIGH/CRITICAL : appelle find_partner_vets() et get_first_aid_steps() si pertinent
- Génère le JSON complet."""

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
