"""
Agent RAG avec Sentence-BERT — DoctoAgent
==========================================
Utilise les embeddings sémantiques pour une recherche
multilingue dans la base de connaissances vétérinaire.

Modèle : paraphrase-multilingual-MiniLM-L12-v2
  - 50+ langues (EN, FR, AR inclus)
  - Taille : 470 MB
  - Recherche sémantique (pas juste mots-clés)

Référence : Reimers & Gurevych (2019)
"""

import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from pydantic import BaseModel

logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────
# CONSTANTES
# ──────────────────────────────────────────────────────────────────
MODEL_NAME               = "paraphrase-multilingual-MiniLM-L12-v2"
HIGH_CONFIDENCE_THRESHOLD = 0.45   # Match sémantique fort
LOW_CONFIDENCE_THRESHOLD  = 0.45   # Match sémantique faible

LOW_CONFIDENCE_WARNING = (
    "\n\n⚠️ Note : Les conseils ci-dessus sont basés sur une correspondance "
    "partielle. Pour des conseils plus précis, consultez un vétérinaire."
)

# ──────────────────────────────────────────────────────────────────
# FALLBACK
# ──────────────────────────────────────────────────────────────────
FALLBACK = {
    "id"             : "fallback",
    "title"          : "Symptômes non identifiés",
    "advice"         : (
        "Je n'ai pas pu identifier précisément les symptômes décrits. "
        "Pour assurer la santé de votre animal, je vous recommande de "
        "consulter un vétérinaire qui pourra l'examiner directement."
    ),
    "home_care"      : [
        "Surveiller attentivement votre animal",
        "Noter tous les symptômes observés (heure, durée, fréquence)",
        "Maintenir alimentation et hydratation normales si possible",
        "Éviter le stress et les changements brusques",
    ],
    "watch_for"      : [
        "Aggravation des symptômes",
        "Apparition de nouveaux signes",
        "Perte d'appétit ou de poids",
        "Léthargie inhabituelle",
    ],
    "when_to_consult": (
        "Consultez un vétérinaire dans les 24-48 heures pour une évaluation. "
        "Si les symptômes s'aggravent (saignements, convulsions, difficultés "
        "respiratoires), rendez-vous immédiatement aux urgences vétérinaires."
    ),
    "preparation"    : [
        "Décrire précisément les symptômes",
        "Noter la chronologie",
        "Lister les changements récents",
        "Préparer l'historique médical",
    ],
    "urgency"        : "MODERATE",
    "source"         : "Conseils généraux - Évaluation vétérinaire recommandée",
    "is_emergency"   : False,
}

# ──────────────────────────────────────────────────────────────────
# MODEL
# ──────────────────────────────────────────────────────────────────
class AdviceResult(BaseModel):
    scenario_id     : str
    title           : str
    advice          : str
    home_care       : List[str]
    watch_for       : List[str]
    when_to_consult : str
    preparation     : List[str]
    urgency         : str
    confidence      : float
    source          : str
    is_emergency    : bool
    is_fallback     : bool  = False
    match_quality   : str   = "high"  # "high", "low", "none"


# ──────────────────────────────────────────────────────────────────
# AGENT RAG SÉMANTIQUE
# ──────────────────────────────────────────────────────────────────
class SemanticRAGAgent:
    """
    Agent RAG utilisant Sentence-BERT pour la recherche sémantique.
    Supporte nativement EN, FR, AR et 47 autres langues.
    """

    def __init__(self, kb_path: Optional[str] = None):
        self.kb            = []
        self.model         = None
        self.kb_embeddings = None
        self.kb_texts      = []

        # Chemin KB
        if kb_path is None:
            base_dir = Path(__file__).resolve().parent.parent
            kb_path  = base_dir / "data" / "vet_advice_kb.json"
        self.kb_path = Path(kb_path)

        self._load_kb()
        self._load_model()
        self._build_embeddings()

    def _load_kb(self):
        """Charge la base de connaissances."""
        try:
            with open(self.kb_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.kb = data.get('scenarios', [])
            logger.info("KB chargée : " + str(len(self.kb)) + " scénarios")
        except Exception as e:
            logger.error("Erreur chargement KB : " + str(e))
            self.kb = []

    def _load_model(self):
        """Charge le modèle Sentence-BERT multilingue."""
        try:
            logger.info("Chargement Sentence-BERT multilingue...")
            self.model = SentenceTransformer(MODEL_NAME)
            logger.info("Sentence-BERT chargé : " + MODEL_NAME)
        except Exception as e:
            logger.error("Erreur chargement Sentence-BERT : " + str(e))
            self.model = None

    def _build_embeddings(self):
        """
        Encode tous les scénarios de la KB en vecteurs sémantiques.
        Ces vecteurs représentent le SENS de chaque scénario.
        """
        if not self.kb or self.model is None:
            return

        # Construire un texte représentatif pour chaque scénario
        # Combinaison de titre + symptômes + mots-clés
        self.kb_texts = []
        for scenario in self.kb:
            text = " ".join([
                scenario.get('title_fr', ''),
                scenario.get('title_en', ''),
                " ".join(scenario.get('trigger_symptoms', [])),
                " ".join(scenario.get('trigger_keywords', [])),
                " ".join(scenario.get('species', [])),
                scenario.get('advice', '')[:100],  # Premier 100 chars du conseil
            ])
            self.kb_texts.append(text)

        # Encoder en vecteurs sémantiques
        logger.info("Encodage de " + str(len(self.kb_texts)) + " scénarios...")
        self.kb_embeddings = self.model.encode(
            self.kb_texts,
            show_progress_bar = False,
            convert_to_numpy  = True,
        )
        logger.info("Embeddings construits : shape " + str(self.kb_embeddings.shape))

    def _build_fallback(self) -> AdviceResult:
        """Retourne un résultat générique quand aucun match."""
        return AdviceResult(
            scenario_id     = FALLBACK['id'],
            title           = FALLBACK['title'],
            advice          = FALLBACK['advice'],
            home_care       = FALLBACK['home_care'],
            watch_for       = FALLBACK['watch_for'],
            when_to_consult = FALLBACK['when_to_consult'],
            preparation     = FALLBACK['preparation'],
            urgency         = FALLBACK['urgency'],
            confidence      = 0.0,
            source          = FALLBACK['source'],
            is_emergency    = FALLBACK['is_emergency'],
            is_fallback     = True,
            match_quality   = "none",
        )

    def search(self, query: str, species: Optional[str] = None,
               top_k: int = 1) -> AdviceResult:
        """
        Cherche le scénario le plus pertinent sémantiquement.

        Args:
            query   : Texte de la requête (n'importe quelle langue)
            species : Espèce optionnelle pour filtrer
            top_k   : Nombre de résultats (1 par défaut)

        Returns:
            AdviceResult le plus pertinent
        """
        if not self.kb or self.model is None or self.kb_embeddings is None:
            logger.warning("RAG non disponible → fallback")
            return self._build_fallback()

        # Encoder la requête avec Sentence-BERT
        query_embedding = self.model.encode(
            [query],
            show_progress_bar = False,
            convert_to_numpy  = True,
        )

        # Calculer similarité cosinus entre requête et tous les scénarios
        similarities = cosine_similarity(query_embedding, self.kb_embeddings)[0]

        # Trier par score décroissant
        ranked_indices = np.argsort(similarities)[::-1]

        # Trouver le meilleur match (avec filtre espèce si fourni)
        for idx in ranked_indices:
            score    = float(similarities[idx])
            scenario = self.kb[idx]

            # Filtrer par espèce si fournie
            if species:
                species_list = [s.lower() for s in scenario.get('species', [])]
                if species.lower() not in species_list:
                    continue

            # Vérifier exclusions
            exclusions = scenario.get('exclusion_keywords', [])
            if any(e.lower() in query.lower() for e in exclusions):
                continue

            # Seuil minimum
            if score < LOW_CONFIDENCE_THRESHOLD:
                logger.info("Score trop faible : " + str(round(score, 2)) + " → fallback")
                return self._build_fallback()

            # Qualité du match
            if score >= HIGH_CONFIDENCE_THRESHOLD:
                match_quality = "high"
                advice = scenario.get('advice', '')
            else:
                match_quality = "low"
                advice = scenario.get('advice', '') + LOW_CONFIDENCE_WARNING

            logger.info(
                "Match trouvé : " + scenario.get('id', '') +
                " (score=" + str(round(score, 2)) + ", qualité=" + match_quality + ")"
            )

            return AdviceResult(
                scenario_id     = scenario.get('id', ''),
                title           = scenario.get('title_fr', scenario.get('title_en', '')),
                advice          = advice,
                home_care       = scenario.get('home_care', []),
                watch_for       = scenario.get('watch_for', []),
                when_to_consult = scenario.get('when_to_consult', ''),
                preparation     = scenario.get('preparation_for_vet', []),
                urgency         = scenario.get('urgency', 'LOW'),
                confidence      = score,
                source          = scenario.get('source', ''),
                is_emergency    = scenario.get('urgency', 'LOW') in ['HIGH', 'CRITICAL'],
                is_fallback     = False,
                match_quality   = match_quality,
            )

        return self._build_fallback()

    def get_advice_for_nlp(self, nlp_result: Dict[str, Any]) -> AdviceResult:
        """
        Méthode principale : prend les résultats NLP et retourne le conseil.
        """
        entities = nlp_result.get('entities', [])
        symptoms = [e.get('text', '') for e in entities if e.get('label') == 'SYMPTOM']
        animals  = [e.get('text', '') for e in entities if e.get('label') == 'ANIMAL']

        # Si aucune entité → fallback direct
        if not symptoms and not animals:
            logger.info("Aucune entité → fallback")
            return self._build_fallback()

        # Construire requête enrichie
        original_text = nlp_result.get('original_text', '')
        translated    = nlp_result.get('translated_text', '')

        # Utiliser le texte traduit si disponible (meilleur pour matching EN)
        text_for_search = original_text
        if translated and len(translated) > 5:
            text_for_search = translated + " " + original_text
        # Ajouter le nom de lespece en anglais explicitement
        if animals:
            query_species = " ".join(animals)
            text_for_search = text_for_search + " " + query_species

        # Ajouter les symptômes extraits
        query = text_for_search + " " + " ".join(symptoms)

        # Identifier l'espèce
        species = animals[0].lower() if animals else None
        species_map = {
            'puppy': 'dog', 'doggy': 'dog',
            'kitten': 'cat', 'kitty': 'cat',
            'budgie': 'bird', 'parrot': 'bird',
        }
        if species in species_map:
            species = species_map[species]

        return self.search(query, species=species)


# ──────────────────────────────────────────────────────────────────
# CONTEXT RAG AGENT (Agentic RAG)
# ──────────────────────────────────────────────────────────────────
_CONTEXT_RAG_PROMPT = """Tu es l'agent de récupération de connaissances de DoctoAgent.

TON RÔLE :
Récupérer TOUTES les données pertinentes de la base de connaissances vétérinaire
pour les symptômes détectés. Les autres agents utiliseront ces données directement
sans avoir besoin d'appeler la KB eux-mêmes.

PROCESSUS :
1. Pour chaque symptôme normalisé, appelle :
   - get_possible_causes(symptôme)     → causes fréquemment associées
   - get_symptom_info(symptôme)        → infos complètes
   - get_red_flags(symptôme)           → signes d'alarme
   - get_home_care(symptôme)           → conseils maison
   - get_evolution_timeline(symptôme)  → évolution attendue
2. Pour l'espèce détectée, appelle :
   - get_species_vulnerabilities(espèce) → vulnérabilités spécifiques
3. Si urgence HIGH/CRITICAL, appelle :
   - get_first_aid_steps(type_urgence) → premiers secours
4. Si intoxication suspectée, appelle :
   - get_toxic_foods(espèce)           → aliments toxiques

OUTILS DISPONIBLES :
- get_possible_causes(symptom_key)
- get_symptom_info(symptom_key)
- get_red_flags(symptom_key)
- get_home_care(symptom_key)
- get_evolution_timeline(symptom_key)
- get_first_aid_steps(emergency_type)
- get_species_vulnerabilities(species)
- get_vaccination_schedule(species, age_months)
- get_breed_specific_risks(breed)
- get_toxic_foods(species)

IMPORTANT : Réponds UNIQUEMENT avec un JSON valide :
{
  "symptoms_data": {
    "<symptôme>": {
      "causes": [...],
      "red_flags": [...],
      "home_care": [...],
      "timeline": {},
      "info": {}
    }
  },
  "species_info": {
    "vulnerabilities": [...],
    "vaccination": {}
  },
  "first_aid": {},
  "breed_risks": {}
}"""


class ContextRAGAgent:
    """
    Agentic RAG : utilise un LLM pour décider quels outils KB appeler,
    fetch toutes les données en une passe, et injecte _kb_context
    dans le contexte pour que PredictionAgent et CareAgent n'aient
    plus besoin d'appeler la KB eux-mêmes.
    """

    def __init__(self):
        from backend.agents.base_llm_agent import BaseLLMAgent
        from backend.agents.tools import RAG_CONTEXT_TOOLS

        class _Inner(BaseLLMAgent):
            name          = "ContextRAGAgent"
            system_prompt = _CONTEXT_RAG_PROMPT
            tools         = RAG_CONTEXT_TOOLS

            def _build_prompt(self, context):
                import json
                symptom_ctx = context.get("_symptom_context", {})
                urgency_ctx = context.get("_urgency_context", {})
                return (
                    f"Récupère les données KB pour :\n"
                    f"- Animal    : {symptom_ctx.get('animal', 'inconnu')}\n"
                    f"- Symptômes : {symptom_ctx.get('symptoms_normalized', [])}\n"
                    f"- Urgence   : {urgency_ctx.get('refined_level', 'LOW')}\n"
                    f"- Red flags : {urgency_ctx.get('red_flags_found', [])}\n\n"
                    f"Appelle les outils KB pour CHAQUE symptôme, puis retourne le JSON."
                )

            def _fallback(self, context, error=""):
                return {"symptoms_data": {}, "species_info": {}, "first_aid": {}, "breed_risks": {}, "status": "fallback"}

        self._agent = _Inner()

    def run(self, context: dict) -> dict:
        return self._agent.run(context)




# ──────────────────────────────────────────────────────────────────
# TESTS
# ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 65)
    print("TEST RAG SÉMANTIQUE — Sentence-BERT Multilingue")
    print("=" * 65)

    tests = [
        # Anglais standard
        {"text": "My dog is vomiting blood", "lang": "EN",
         "entities": [{"text": "dog", "label": "ANIMAL"}, {"text": "vomiting", "label": "SYMPTOM"}, {"text": "blood", "label": "SYMPTOM"}]},

        # Variation linguistique (throwing up)
        {"text": "My dog has been throwing up all morning", "lang": "EN (variation)",
         "entities": [{"text": "dog", "label": "ANIMAL"}, {"text": "throwing up", "label": "SYMPTOM"}]},

        # Français
        {"text": "Mon chat ne mange plus depuis 2 jours", "lang": "FR",
         "entities": [{"text": "cat", "label": "ANIMAL"}, {"text": "ne mange plus", "label": "SYMPTOM"}]},

        # Arabe
        {"text": "كلبي أكل سماً ساعدني", "lang": "AR",
         "entities": [{"text": "dog", "label": "ANIMAL"}, {"text": "poison", "label": "SYMPTOM"}]},

        # Lapin urgent
        {"text": "My rabbit stopped eating since yesterday", "lang": "EN",
         "entities": [{"text": "rabbit", "label": "ANIMAL"}, {"text": "stopped eating", "label": "SYMPTOM"}]},

        # Hors scope
        {"text": "What is the weather today?", "lang": "Hors scope",
         "entities": []},

        # Symptôme rare
        {"text": "My dog snores loudly every night", "lang": "EN (rare)",
         "entities": [{"text": "dog", "label": "ANIMAL"}, {"text": "snores", "label": "SYMPTOM"}]},
    ]

    for i, test in enumerate(tests, 1):
        nlp_result = {
            "original_text": test["text"],
            "entities"     : test["entities"],
        }

        print("\n--- Test " + str(i) + " [" + test["lang"] + "] ---")
        print("Texte : " + test["text"])

        result = rag_agent.get_advice_for_nlp(nlp_result)

        print("Scénario   : " + result.title)
        print("Urgence    : " + result.urgency)
        print("Confiance  : " + str(round(result.confidence, 2)))
        print("Qualité    : " + result.match_quality.upper())
        print("Fallback   : " + ("OUI" if result.is_fallback else "NON"))
        print("Source     : " + result.source)
        print("-" * 65)
