"""
DoctoAgent — Validation Agent (LLM-powered)  [EXT]
====================================================
Agent de contrôle qualité du pipeline.

Rôle : évaluer la cohérence globale des résultats produits par les
agents précédents. L'agent pense comme un auditeur médical : il vérifie
que tout est cohérent avant que la réponse ne soit envoyée à l'utilisateur.

Il peut consulter la KB pour vérifier si les causes prédites
correspondent bien aux symptômes détectés.

Auteur : Rim Hajji — PFE 2026
"""

import json
from typing import Any, Dict

from backend.agents.base_llm_agent import BaseLLMAgent
from backend.agents.tools import VALIDATION_TOOLS

SYSTEM_PROMPT = """Tu es un auditeur qualité pour DoctoAgent.

CONTEXTE IMPORTANT :
DoctoAgent est un système de CONSEILS PRÉVENTIFS et d'ORIENTATION vétérinaire.
Il ne pose PAS de diagnostic médical. Les "causes possibles" identifiées
sont des pistes d'orientation, pas des diagnostics.

TON RÔLE :
Vérifier que la réponse du pipeline est cohérente, sûre, et appropriée
avant qu'elle soit envoyée à l'utilisateur.

CONTRÔLES À EFFECTUER :
1. QUALITÉ DES ENTITÉS : des symptômes ou un animal ont-ils été détectés ?
2. COHÉRENCE URGENCE : le niveau d'urgence est-il justifié par les symptômes ?
   Si nécessaire, appelle get_red_flags(symptôme) pour vérifier
3. PERTINENCE DES PISTES : les conditions associées sont-elles cohérentes avec
   les symptômes ? Appelle get_symptom_info(symptôme) si nécessaire.
   Si une condition est douteuse → appelle get_symptom_info(symptôme) pour vérifier
4. INTÉGRITÉ DU TEXTE : le texte est-il assez long et clair pour une analyse ?
5. SÉCURITÉ DU CONSEIL : le pipeline oriente-t-il bien vers un vétérinaire
   quand c'est nécessaire (HIGH/CRITICAL) ? Vérifie que aucun "diagnostic" ferme
   n'est posé — seules des pistes préventives sont acceptables.

NIVEAUX DE SÉVÉRITÉ DES PROBLÈMES :
- ERROR   : problème bloquant (texte vide, aucune entité détectée)
- WARNING : incohérence non bloquante (urgence suspecte, prédictions faibles)

QUALITÉ GLOBALE :
- GOOD       : ≥ 4/5 checks OK, aucune ERROR
- ACCEPTABLE : 3/5 checks OK, ou 1+ WARNING
- POOR       : < 3/5 checks OK, ou 1+ ERROR

OUTILS DISPONIBLES (utilise UNIQUEMENT ces outils, aucun autre) :
- list_kb_symptoms()             : liste toutes les clés de la KB
- get_symptom_info(symptom_key)  : infos complètes d'un symptôme KB
- get_red_flags(symptom_key)     : red flags d'un symptôme KB

IMPORTANT : Réponds UNIQUEMENT avec un objet JSON valide :
{
  "is_valid": true/false,
  "overall_quality": "GOOD | ACCEPTABLE | POOR",
  "pipeline_score": 0.0-1.0,
  "checks_passed": 0-5,
  "checks_total": 5,
  "issues": [
    {
      "check_id": "CHECK-1 à CHECK-5",
      "severity": "ERROR | WARNING",
      "description": "description du problème",
      "suggestion": "suggestion de correction ou null"
    }
  ],
  "corrections": ["correction appliquée 1", ...],
  "validation_summary": "résumé de l'audit",
  "confidence": 0.0-1.0
}"""


class ValidationAgent(BaseLLMAgent):
    name          = "ValidationAgent"
    system_prompt = SYSTEM_PROMPT
    tools         = VALIDATION_TOOLS

    def _build_prompt(self, context: Dict[str, Any]) -> str:
        symptom_ctx    = context.get("_symptom_context", {})
        urgency_ctx    = context.get("_urgency_context", {})
        prediction_ctx = context.get("_prediction_context", {})

        causes_summary = []
        for c in prediction_ctx.get("possible_associations", [])[:3]:
            if isinstance(c, dict):
                causes_summary.append(
                    f"{c.get('condition')} (fréquence={c.get('frequency')}, "
                    f"vet={c.get('requires_vet')})"
                )

        return f"""Audite la cohérence de l'analyse suivante :

TEXTE ORIGINAL : "{context.get("original_text", "")}"
(longueur : {len(context.get("original_text", ""))} caractères)

--- RÉSULTATS SYMPTOM AGENT ---
Animal              : {symptom_ctx.get("animal")}
Symptômes normalisés: {symptom_ctx.get("symptoms_normalized", [])}
Indicateurs sévérité: {symptom_ctx.get("severity_indicators", [])}
Confidence          : {symptom_ctx.get("confidence", 0)}

--- RÉSULTATS URGENCY AGENT ---
Niveau NLP          : {urgency_ctx.get("nlp_level", context.get("urgency_label", "LOW"))}
Niveau raffiné      : {urgency_ctx.get("refined_level", "LOW")}
Escaladé            : {urgency_ctx.get("was_escalated", False)}
Red flags trouvés   : {urgency_ctx.get("red_flags_found", [])}
Confidence          : {urgency_ctx.get("confidence", 0)}

--- RÉSULTATS ORIENTATION AGENT ---
Préoccupation princ.: {prediction_ctx.get("main_concern")}
Délai surveillance  : {prediction_ctx.get("watch_delay")}
Nb associations     : {len(prediction_ctx.get("possible_associations", []))}
Top 3 associations  : {causes_summary}
KB coverage         : {prediction_ctx.get("kb_coverage", 0)}
Résumé orientation  : {prediction_ctx.get("orientation_summary", "")}
Confidence          : {prediction_ctx.get("confidence", 0)}

--- SCORES NLP BRUTS ---
Intent confidence   : {context.get("intent_confidence", 0):.2f}
Urgency confidence  : {context.get("urgency_confidence", 0):.2f}

Vérifie la cohérence, utilise les outils si nécessaire pour valider,
et retourne le JSON d'audit."""

    def _fallback(self, context: Dict[str, Any], error: str = "") -> Dict[str, Any]:
        return {
            "is_valid"          : True,
            "overall_quality"   : "ACCEPTABLE",
            "pipeline_score"    : 0.5,
            "checks_passed"     : 3,
            "checks_total"      : 5,
            "issues"            : [],
            "corrections"       : [],
            "validation_summary": "Validation non effectuée — résultat par défaut.",
            "confidence"        : 0.5,
            "status"            : "fallback",
        }
