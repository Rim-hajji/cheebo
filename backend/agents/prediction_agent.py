"""
DoctoAgent — Symptom Orientation Agent (LLM-powered)
======================================================
Agent d'orientation : identifie les pistes possibles à surveiller
et à mentionner au vétérinaire. Ne pose PAS de diagnostic.

Rôle : à partir des symptômes normalisés, consulte la KB pour
identifier les conditions fréquemment associées à ces signes,
et produit des conseils de surveillance temporisée
("si ça persiste X jours → consultez un vétérinaire").

Auteur : Rim Hajji — PFE 2026
"""

import json
from typing import Any, Dict

from backend.agents.base_llm_agent import BaseLLMAgent
from backend.agents.tools import PREDICTION_TOOLS  # inclut web_search_vet + search_wikipedia_vet

SYSTEM_PROMPT = """Tu es un assistant d'orientation vétérinaire pour DoctoAgent.

⚠️ RÈGLE ABSOLUE :
DoctoAgent ne pose PAS de diagnostic médical.
Tu fournis des CONSEILS PRÉVENTIFS et tu ORIENTES vers le vétérinaire.
Un vétérinaire seul peut poser un diagnostic après examen clinique.

TON RÔLE :
Analyser les symptômes décrits et identifier les conditions auxquelles
ils sont fréquemment associés — uniquement pour aider le propriétaire à :
  1. Comprendre la gravité potentielle de la situation
  2. Savoir QUAND consulter un vétérinaire (maintenant, sous 24h, sous 48h…)
  3. Savoir QUOI surveiller à domicile en attendant

PROCESSUS À SUIVRE :
1. Les données KB sont DÉJÀ disponibles dans le champ KB_CONTEXT du prompt — utilise-les directement
2. Si un symptôme est absent du KB_CONTEXT :
   → appelle web_search_vet("symptôme espèce signes associés")
   → ou appelle search_wikipedia_vet(condition_possible)
3. Croise les associations pour identifier la préoccupation principale
4. Détermine un délai de surveillance avant consultation vétérinaire

FORMULATIONS CORRECTES (à utiliser) :
✅ "Ces symptômes sont fréquemment associés à..."
✅ "Si ces signes persistent plus de [X], consultez un vétérinaire"
✅ "À surveiller : si vous observez [signe], consultez immédiatement"
✅ "Ces signes méritent l'attention d'un vétérinaire pour confirmer"

FORMULATIONS INTERDITES (à ne jamais utiliser) :
❌ "Votre animal a [maladie]"
❌ "Le diagnostic est..."
❌ "Il souffre de..."
❌ "C'est certainement..."

DÉLAIS DE SURVEILLANCE à proposer selon l'urgence :
- LOW      : surveiller 2-3 jours, consulter si ça persiste
- MODERATE : consulter sous 24-48h si pas d'amélioration
- HIGH     : consultation aujourd'hui
- CRITICAL : urgence immédiate, ne pas attendre

OUTILS DISPONIBLES (uniquement pour les symptômes absents du KB_CONTEXT) :
- web_search_vet(query)        : recherche DuckDuckGo vétérinaire
- search_wikipedia_vet(topic)  : recherche Wikipedia vétérinaire

IMPORTANT : Réponds UNIQUEMENT avec un objet JSON valide :
{
  "possible_associations": [
    {
      "condition": "nom de la condition fréquemment associée",
      "frequency": "HIGH | MEDIUM | LOW",
      "source_symptoms": ["symptôme1", "symptôme2"],
      "requires_vet": true/false,
      "urgency_hint": "LOW | MODERATE | HIGH | CRITICAL",
      "watch_for": "signe qui doit déclencher une consultation immédiate"
    }
  ],
  "main_concern": "préoccupation principale à surveiller",
  "watch_delay": "délai de surveillance avant consultation (ex: 48h, immédiat)",
  "symptoms_analyzed": ["symptôme1", ...],
  "kb_coverage": 0.0-1.0,
  "vet_consultation_needed": true/false,
  "confidence": 0.0-1.0,
  "orientation_summary": "conseil de surveillance en 1-2 phrases, langage propriétaire"
}"""


class PredictionAgent(BaseLLMAgent):
    name          = "PredictionAgent"
    system_prompt = SYSTEM_PROMPT
    tools         = PREDICTION_TOOLS

    def _build_prompt(self, context: Dict[str, Any]) -> str:
        symptom_ctx = context.get("_symptom_context", {})
        urgency_ctx = context.get("_urgency_context", {})
        kb_context  = context.get("_kb_context", {})
        normalized  = symptom_ctx.get("symptoms_normalized", [])

        return f"""Analyse les symptômes suivants et oriente le propriétaire :

TEXTE ORIGINAL : {context.get("original_text", "")}

SITUATION :
- Animal               : {symptom_ctx.get("animal", "inconnu")}
- Symptômes normalisés : {normalized}
- Durée                : {symptom_ctx.get("duration", "non précisée")}
- Niveau d'urgence     : {urgency_ctx.get("refined_level", context.get("urgency_label", "LOW"))}
- Signes d'alerte      : {urgency_ctx.get("red_flags_found", [])}

KB_CONTEXT (données vétérinaires pré-chargées) :
{json.dumps(kb_context, ensure_ascii=False, indent=2)}

Utilise les données KB_CONTEXT directement. Appelle web_search_vet uniquement
si un symptôme est absent du KB_CONTEXT. Produis le JSON d'orientation."""

    # Correspondance symptômes NLP → clés KB
    _SYMPTOM_KB_MAP = {
        "vomit": "vomissement", "vomissement": "vomissement", "vomiting": "vomissement",
        "diarrhée": "diarrhée", "diarrhea": "diarrhée",
        "toux": "toux", "cough": "toux", "coughing": "toux",
        "convulsion": "convulsion", "seizure": "convulsion",
        "boiterie": "boiterie", "limp": "boiterie", "limping": "boiterie",
        "apathie": "apathie", "léthargie": "apathie", "lethargy": "apathie",
        "lethargic": "apathie", "fatigue": "apathie", "apathy": "apathie",
        "démangeaison": "démangeaison", "itching": "démangeaison", "scratching": "démangeaison",
        "oeil rouge": "oeil rouge", "écoulement oculaire": "oeil rouge", "watery eyes": "oeil rouge",
        "écoulement nasal": "écoulement nasal", "runny nose": "écoulement nasal",
        "ventre gonflé": "ventre gonflé", "swollen belly": "ventre gonflé",
        "perte de poils": "perte de poils", "hair loss": "perte de poils",
        "mauvaise haleine": "mauvaise haleine", "bad breath": "mauvaise haleine",
        "sang dans les urines": "sang dans les urines", "blood in urine": "sang dans les urines",
        "anorexie": "vomissement", "not eating": "vomissement", "perte d'appétit": "vomissement",
        "fever": "fièvre", "fièvre": "fièvre", "température élevée": "fièvre",
        "poison": "intoxication", "poisoning": "intoxication", "intoxication": "intoxication",
        "difficulty breathing": "difficultés respiratoires", "respiration difficile": "difficultés respiratoires",
        "heat stroke": "coup de chaleur", "coup de chaleur": "coup de chaleur",
        "shock": "choc", "collapse": "choc", "choc": "choc",
        "fracture": "fracture", "broken bone": "fracture",
        "bite": "morsure", "morsure": "morsure",
        "allergy": "allergie", "allergic": "allergie", "allergie": "allergie",
        "diabetes": "diabète", "diabète": "diabète",
        "kidney failure": "insuffisance rénale", "insuffisance rénale": "insuffisance rénale",
        "gi stasis": "stase digestive", "stase digestive": "stase digestive",
        "mange": "gale", "gale": "gale",
        "paralysis": "paralysie", "paralysie": "paralysie",
        "dehydration": "déshydratation", "déshydratation": "déshydratation",
        "nosebleed": "épistaxis", "épistaxis": "épistaxis",
        "jaunisse": "jaunisse", "jaundice": "jaunisse", "ictère": "jaunisse",
        "abcès": "abcès", "abscess": "abcès",
        "otite": "otite", "ear infection": "otite",
        "polyurie": "polyurie", "urination excessive": "polyurie",
        "dysurie": "dysurie", "difficulty urinating": "dysurie", "straining to urinate": "dysurie",
        "masse cutanée": "masse cutanée", "skin lump": "masse cutanée", "tumeur": "masse cutanée",
        "halètement": "halètement excessif", "panting": "halètement excessif",
        "prurit anal": "prurit anal", "anal itching": "prurit anal", "scooting": "prurit anal",
        "larmoiement": "larmoiement", "eye discharge": "larmoiement",
        "ascite": "ascite", "ascites": "ascite",
        "toux du chenil": "toux du chenil", "kennel cough": "toux du chenil",
        "parvovirose": "parvovirose", "parvovirus": "parvovirose", "parvo": "parvovirose",
        "syndrome vestibulaire": "syndrome vestibulaire", "vestibular": "syndrome vestibulaire", "head tilt": "syndrome vestibulaire",
        "éternuements": "éternuements", "sneezing": "éternuements", "rhinite": "éternuements",
    }

    def _kb_associations(self, symptoms: list) -> list:
        """Construit les associations depuis la KB sans LLM."""
        from backend.agents.tools import _KB
        associations = []
        seen_kb_keys = set()
        for sym in symptoms:
            kb_key = self._SYMPTOM_KB_MAP.get(sym.lower())
            if not kb_key or kb_key in seen_kb_keys:
                continue
            entry = _KB.get(kb_key, {})
            if not entry:
                continue
            seen_kb_keys.add(kb_key)
            causes   = entry.get("causes_possibles", [])
            red_flags = entry.get("red_flags", [])
            for i, cause in enumerate(causes[:2]):
                associations.append({
                    "condition"      : cause,
                    "frequency"      : "HIGH" if i == 0 else "MEDIUM",
                    "source_symptoms": [sym],
                    "requires_vet"   : True,
                    "urgency_hint"   : "MODERATE",
                    "watch_for"      : red_flags[0] if red_flags else "",
                })
        return associations

    def _fallback(self, context: Dict[str, Any], error: str = "") -> Dict[str, Any]:
        urgency = context.get("_urgency_context", {}).get(
            "refined_level", context.get("urgency_label", "LOW")
        )
        delay_map = {
            "LOW": "2-3 jours", "MODERATE": "24-48h",
            "HIGH": "aujourd'hui", "CRITICAL": "immédiatement",
        }
        symptoms = context.get("_symptom_context", {}).get("symptoms_normalized", [])
        associations = self._kb_associations(symptoms)
        main_concern = associations[0]["condition"] if associations else "Symptômes à surveiller"

        return {
            "possible_associations" : associations,
            "main_concern"          : main_concern,
            "watch_delay"           : delay_map.get(urgency, "48h"),
            "symptoms_analyzed"     : symptoms,
            "kb_coverage"           : 0.5 if associations else 0.0,
            "vet_consultation_needed": True,
            "confidence"            : 0.3,
            "orientation_summary"   : (
                f"Ces symptômes sont fréquemment associés à {main_concern}. "
                f"Consultez un vétérinaire {delay_map.get(urgency, 'dans les 48h')}."
                if associations else
                "Surveillance recommandée. Consultez un vétérinaire si les symptômes persistent."
            ),
            "status": "fallback",
        }
