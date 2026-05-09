"""
DoctoAgent — Orchestrator (LangGraph + LLM Agents)
====================================================
Coordonne le pipeline multi-agents via un LangGraph StateGraph.
Chaque nœud est un vrai agent LLM (Gemini + outils) qui raisonne,
appelle des outils, et prend une décision autonome.

Flux du graphe (linéaire — plus de routing conditionnel) :
  START
    ↓
  [context_rag_node]      ← ContextRAGAgent    : fetch toutes les données KB en une passe
    ↓
  [prediction_node]       ← PredictionAgent    : orientation + associations symptômes
    ↓
  [rag_node]              ← SemanticRAGAgent   : recherche sémantique Sentence-BERT
    ↓
  [recommendation_node]   ← RecommendationAgent: care + emergency + recommandation (unifié)
    ↓
  [aggregate_node]        ← Aggregator         : fusionne tous les contextes
    ↓
  [synthesis_node]        ← SynthesisAgent     : réponse conversationnelle finale
    ↓
  END

Auteur : Rim Hajji — PFE 2026
"""

import logging
from typing import Any, Dict, Optional

from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph

from backend.agents.aggregator            import Aggregator
from backend.agents.prediction_agent      import PredictionAgent
from backend.agents.rag_agent             import ContextRAGAgent, SemanticRAGAgent
from backend.agents.recommendation_agent  import RecommendationAgent
from backend.agents.synthesis_agent       import SynthesisAgent
from backend.agents.tools                 import init_kb

logger = logging.getLogger("doctoagent.orchestrator")

# ──────────────────────────────────────────────────────────────────
# PRÉTRAITEMENT NLP → remplace SymptomAgent + UrgencyAgent
# ──────────────────────────────────────────────────────────────────
_SYMPTOM_KB_MAP = {
    "vomit": "vomissement", "vomissement": "vomissement", "vomiting": "vomissement",
    "diarrhée": "diarrhée", "diarrhea": "diarrhée",
    "toux": "toux", "cough": "toux", "coughing": "toux",
    "convulsion": "convulsion", "seizure": "convulsion",
    "boiterie": "boiterie", "limp": "boiterie", "limping": "boiterie",
    "apathie": "apathie", "léthargie": "apathie", "lethargy": "apathie",
    "lethargic": "apathie", "fatigue": "apathie",
    "démangeaison": "démangeaison", "itching": "démangeaison", "scratching": "démangeaison",
    "oeil rouge": "oeil rouge", "écoulement oculaire": "oeil rouge", "watery eyes": "oeil rouge",
    "écoulement nasal": "écoulement nasal", "runny nose": "écoulement nasal",
    "ventre gonflé": "ventre gonflé", "bloat": "ventre gonflé", "swollen belly": "ventre gonflé",
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
    "dysurie": "dysurie", "difficulty urinating": "dysurie",
    "masse cutanée": "masse cutanée", "skin lump": "masse cutanée", "tumeur": "masse cutanée",
    "halètement": "halètement excessif", "panting": "halètement excessif",
    "prurit anal": "prurit anal", "scooting": "prurit anal",
    "larmoiement": "larmoiement", "eye discharge": "larmoiement",
    "ascite": "ascite", "ascites": "ascite",
    "toux du chenil": "toux du chenil", "kennel cough": "toux du chenil",
    "parvovirose": "parvovirose", "parvovirus": "parvovirose", "parvo": "parvovirose",
    "syndrome vestibulaire": "syndrome vestibulaire", "head tilt": "syndrome vestibulaire",
    "éternuements": "éternuements", "sneezing": "éternuements", "rhinite": "éternuements",
}

_URGENCY_LABELS = {
    "LOW"     : "Surveillance à domicile",
    "MODERATE": "Consultation conseillée sous 48h",
    "HIGH"    : "Consultation urgente recommandée",
    "CRITICAL": "Urgence vétérinaire immédiate",
}
_URGENCY_SCORES = {"LOW": 1, "MODERATE": 4, "HIGH": 7, "CRITICAL": 10}


def _preprocess_nlp(nlp_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remplace SymptomAgent + UrgencyAgent.
    Construit _symptom_context et _urgency_context directement
    depuis les sorties du pipeline NLP — aucun appel LLM.
    """
    entities = nlp_dict.get("entities", [])

    # Normalisation des symptômes (NLP entity → clé KB)
    symptoms_raw        = [e.get("text", "") for e in entities if e.get("label") == "SYMPTOM"]
    symptoms_normalized = list(dict.fromkeys(
        _SYMPTOM_KB_MAP.get(s.lower(), s) for s in symptoms_raw
    ))
    animal   = next((e.get("normalized", e.get("text", "")) for e in entities if e.get("label") == "ANIMAL"), "inconnu")
    duration = next((e.get("text", "") for e in entities if e.get("label") == "DURATION"), None)

    symptom_ctx = {
        "animal"             : animal,
        "animal_raw"         : animal,
        "symptoms_raw"       : symptoms_raw,
        "symptoms_normalized": symptoms_normalized,
        "duration"           : duration,
        "severity_indicators": [],
        "has_severity_flag"  : False,
        "symptom_count"      : len(symptoms_normalized),
        "confidence"         : 0.85,
    }

    # Urgence passthrough depuis le NLP (modèle déjà entraîné)
    level = nlp_dict.get("urgency_label", "LOW")
    urgency_ctx = {
        "nlp_level"          : level,
        "refined_level"      : level,
        "refined_score"      : _URGENCY_SCORES.get(level, 1),
        "label"              : _URGENCY_LABELS.get(level, level),
        "was_escalated"      : False,
        "was_downgraded"     : False,
        "escalation_triggers": [],
        "red_flags_found"    : [],
        "reasoning_steps"    : ["Niveau NLP direct — modèle entraîné"],
        "confidence"         : nlp_dict.get("urgency_confidence", 0.75),
    }

    nlp_dict["_symptom_context"] = symptom_ctx
    nlp_dict["_urgency_context"] = urgency_ctx
    return nlp_dict, symptom_ctx, urgency_ctx


SAFETY_WARNING = (
    "⚕️ DoctoAgent est un outil d'aide à la décision. Ses recommandations "
    "ne remplacent pas l'avis d'un vétérinaire professionnel."
)


# ──────────────────────────────────────────────────────────────────
# ÉTAT PARTAGÉ DU GRAPHE
# ──────────────────────────────────────────────────────────────────
class DoctoAgentState(TypedDict):
    nlp_dict               : Dict[str, Any]
    symptom_context        : Dict[str, Any]
    urgency_context        : Dict[str, Any]
    kb_context             : Dict[str, Any]   # ContextRAGAgent — données KB centralisées
    prediction_context     : Dict[str, Any]
    validation_context     : Dict[str, Any]
    emergency_context      : Dict[str, Any]   # extrait de recommendation_context
    care_context           : Dict[str, Any]   # extrait de recommendation_context
    rag_context            : Dict[str, Any]
    recommendation_context : Dict[str, Any]
    synthesis_context      : Dict[str, Any]
    urgency_level          : str
    is_emergency           : bool
    agent_timings          : Dict[str, float]
    final_response         : Dict[str, Any]


# ──────────────────────────────────────────────────────────────────
# NŒUDS DU GRAPHE
# Chaque nœud : lit l'état → appelle l'agent LLM → met à jour l'état
# ──────────────────────────────────────────────────────────────────


def make_context_rag_node(agent: ContextRAGAgent):
    def context_rag_node(state: DoctoAgentState) -> Dict:
        """Fetch toutes les données KB en une passe — injecte _kb_context."""
        nlp_dict = dict(state["nlp_dict"])
        result   = agent.run(nlp_dict)
        result.pop("_agent_name", None)
        result.pop("_processing_ms", None)
        result.pop("status", None)
        nlp_dict["_kb_context"] = result
        return {
            "nlp_dict"    : nlp_dict,
            "kb_context"  : result,
            "agent_timings": {
                **state.get("agent_timings", {}),
                "ContextRAGAgent": state.get("agent_timings", {}).get("ContextRAGAgent", 0),
            },
        }
    return context_rag_node


def make_prediction_node(agent: PredictionAgent):
    def prediction_node(state: DoctoAgentState) -> Dict:
        nlp_dict = dict(state["nlp_dict"])
        result   = agent.run(nlp_dict)

        nlp_dict["_prediction_context"] = result
        return {
            "nlp_dict"          : nlp_dict,
            "prediction_context": result,
            "agent_timings"     : {
                **state.get("agent_timings", {}),
                "PredictionAgent": result.get("_processing_ms", 0),
            },
        }
    return prediction_node



def make_recommendation_node(agent: RecommendationAgent):
    def recommendation_node(state: DoctoAgentState) -> Dict:
        nlp_dict = dict(state["nlp_dict"])
        result   = agent.run(nlp_dict)

        # Extraire les sous-contextes pour la compatibilité avec l'aggregator
        emergency_ctx = {
            "is_emergency"    : result.get("is_emergency", False),
            "urgency_level"   : result.get("urgency_level", "LOW"),
            "alert_message"   : result.get("alert_message"),
            "immediate_actions": result.get("immediate_actions", []),
            "partner_vets"    : result.get("partner_vets", []),
            "should_redirect" : result.get("should_redirect", False),
            "safety_warning"  : result.get("safety_warning", ""),
            "confidence"      : result.get("confidence", 0.5),
        }
        care_ctx = {
            "care_plan"        : result.get("care_plan", {}),
            "urgency_level"    : result.get("urgency_level", "LOW"),
            "kb_symptoms_found": result.get("kb_symptoms_found", []),
            "care_summary"     : result.get("care_summary", ""),
            "confidence"       : result.get("confidence", 0.5),
        }
        recommendation_ctx = {
            "message"      : result.get("message", ""),
            "actions"      : result.get("actions", []),
            "warnings"     : result.get("warnings", []),
            "next_steps"   : result.get("next_steps", ""),
            "severity"     : result.get("urgency_level", "LOW"),
            "should_consult": result.get("should_consult", True),
        }

        return {
            "recommendation_context": recommendation_ctx,
            "emergency_context"     : emergency_ctx,
            "care_context"          : care_ctx,
            "is_emergency"          : result.get("is_emergency", False),
            "agent_timings"         : {
                **state.get("agent_timings", {}),
                "RecommendationAgent": result.get("_processing_ms", 0),
            },
        }
    return recommendation_node


def make_rag_node(agent: SemanticRAGAgent):
    def rag_node(state: DoctoAgentState) -> Dict:
        try:
            result = agent.get_advice_for_nlp(state["nlp_dict"])
            ctx = result.model_dump() if hasattr(result, "model_dump") else vars(result)
        except Exception as e:
            logger.warning(f"RAGAgent erreur : {e}")
            ctx = {}
        return {"rag_context": ctx}
    return rag_node


def make_aggregate_node(aggregator: Aggregator):
    def aggregate_node(state: DoctoAgentState) -> Dict:
        """Fusionne tous les contextes en réponse finale."""
        response = aggregator.aggregate_from_dicts(
            nlp_dict               = state["nlp_dict"],
            symptom_ctx            = state.get("symptom_context", {}),
            urgency_ctx            = state.get("urgency_context", {}),
            prediction_ctx         = state.get("prediction_context", {}),
            validation_ctx         = state.get("validation_context", {}),
            emergency_ctx          = state.get("emergency_context", {}),
            care_ctx               = state.get("care_context", {}),
            rag_ctx                = state.get("rag_context", {}),
            recommendation_ctx     = state.get("recommendation_context", {}),
            agent_timings          = state.get("agent_timings", {}),
        )
        return {"final_response": response}
    return aggregate_node


def make_synthesis_node(agent: SynthesisAgent):
    def synthesis_node(state: DoctoAgentState) -> Dict:
        """Génère la réponse conversationnelle finale via Gemini (remplace les templates statiques)."""
        result = agent.run(state["final_response"])
        updated = dict(state["final_response"])
        updated["synthesis"] = result
        return {
            "synthesis_context": result,
            "final_response"   : updated,
            "agent_timings"    : {
                **state.get("agent_timings", {}),
                "SynthesisAgent": result.get("_processing_ms", 0),
            },
        }
    return synthesis_node


# ──────────────────────────────────────────────────────────────────
# ORCHESTRATEUR
# ──────────────────────────────────────────────────────────────────
class Orchestrator:
    """
    Orchestre le pipeline multi-agents DoctoAgent via LangGraph.
    Chaque agent est un vrai LLM (Gemini) qui raisonne et utilise des outils.
    """

    def __init__(self, kb_data: Optional[Dict] = None):
        kb = kb_data or {}
        logger.info("Initialisation Orchestrateur DoctoAgent (LangGraph + LLM Agents)...")

        # Injecter la KB dans les outils partagés
        init_kb(kb)

        # Instancier les agents
        self._context_rag_agent    = ContextRAGAgent()       # Agentic RAG — fetch KB centralisé
        self._prediction_agent     = PredictionAgent()       # Orientation + associations
        self._rag_agent            = SemanticRAGAgent()      # Sentence-BERT semantic search
        self._recommendation_agent = RecommendationAgent()   # Care + Emergency + Recommendation
        self._synthesis_agent      = SynthesisAgent()
        self._aggregator           = Aggregator()

        self._graph = self._build_graph()
        logger.info("Graphe LangGraph compilé — 3 agents LLM : ContextRAG → Prediction → Recommendation.")

    def _build_graph(self):
        graph = StateGraph(DoctoAgentState)

        graph.add_node("context_rag_node",    make_context_rag_node(self._context_rag_agent))
        graph.add_node("prediction_node",     make_prediction_node(self._prediction_agent))
        graph.add_node("rag_node",            make_rag_node(self._rag_agent))
        graph.add_node("recommendation_node", make_recommendation_node(self._recommendation_agent))
        graph.add_node("aggregate_node",      make_aggregate_node(self._aggregator))
        graph.add_node("synthesis_node",      make_synthesis_node(self._synthesis_agent))

        # Flux linéaire — plus de routing conditionnel
        graph.add_edge(START,                 "context_rag_node")
        graph.add_edge("context_rag_node",    "prediction_node")
        graph.add_edge("prediction_node",     "rag_node")
        graph.add_edge("rag_node",            "recommendation_node")
        graph.add_edge("recommendation_node", "aggregate_node")
        graph.add_edge("aggregate_node",      "synthesis_node")
        graph.add_edge("synthesis_node",      END)

        return graph.compile()

    # ─────────────────────────────────────────
    def handle(self, nlp_result: Any) -> Dict[str, Any]:
        nlp_dict = self._to_dict(nlp_result)

        # Prétraitement direct — remplace SymptomAgent + UrgencyAgent
        nlp_dict, symptom_ctx, urgency_ctx = _preprocess_nlp(nlp_dict)

        logger.info(
            f"Pipeline démarré | intent={nlp_dict.get('intent')} | "
            f"urgency={nlp_dict.get('urgency_label')} | "
            f"symptoms={nlp_dict['_symptom_context'].get('symptoms_normalized')} | "
            f"'{nlp_dict.get('original_text','')[:50]}...'"
        )

        initial_state: DoctoAgentState = {
            "nlp_dict"              : nlp_dict,
            "symptom_context"       : symptom_ctx,
            "urgency_context"       : urgency_ctx,
            "kb_context"            : {},
            "prediction_context"    : {},
            "validation_context"    : {},
            "emergency_context"     : {},
            "care_context"          : {},
            "rag_context"           : {},
            "recommendation_context": {},
            "synthesis_context"     : {},
            "urgency_level"         : nlp_dict.get("urgency_label", "LOW"),
            "is_emergency"          : False,
            "agent_timings"         : {},
            "final_response"        : {},
        }

        try:
            final_state = self._graph.invoke(initial_state)
            response    = final_state.get("final_response", {})
            if not response:
                return self._error_response("Réponse vide.", nlp_dict)
            logger.info(
                f"Pipeline terminé | urgence={final_state.get('urgency_level')} | "
                f"emergency={final_state.get('is_emergency')}"
            )
            return response
        except Exception as e:
            logger.error(f"Erreur critique : {e}", exc_info=True)
            return self._error_response(str(e), nlp_dict)

    def get_graph_diagram(self) -> str:
        """Diagramme Mermaid du graphe (pour la doc PFE)."""
        try:
            return self._graph.get_graph().draw_mermaid()
        except Exception:
            return "Diagramme non disponible."

    @staticmethod
    def _to_dict(nlp_result: Any) -> Dict[str, Any]:
        if isinstance(nlp_result, dict):
            return nlp_result
        if hasattr(nlp_result, "model_dump"):
            return nlp_result.model_dump()
        if hasattr(nlp_result, "dict"):
            return nlp_result.dict()
        return vars(nlp_result)

    @staticmethod
    def _error_response(error: str, nlp_dict: Dict) -> Dict:
        return {
            "status"           : "error",
            "error"            : error,
            "main_message"     : "Erreur d'analyse. Consultez directement un vétérinaire.",
            "urgency"          : {"level": nlp_dict.get("urgency_label", "MODERATE")},
            "emergency"        : {"is_emergency": False},
            "safety_disclaimer": SAFETY_WARNING,
        }
