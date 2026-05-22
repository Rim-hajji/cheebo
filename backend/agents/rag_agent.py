"""
Agent RAG avec ChromaDB — DoctoAgent
======================================
Recherche sémantique multilingue dans la base de connaissances
vétérinaire via ChromaDB (vecteurs persistants, index HNSW).

Modèle d'embedding : paraphrase-multilingual-MiniLM-L12-v2
  - 50+ langues (EN, FR, AR inclus)
  - Persistance sur disque — pas de recalcul au redémarrage

Référence : Reimers & Gurevych (2019)
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from pydantic import BaseModel

logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────
# CONSTANTES
# ──────────────────────────────────────────────────────────────────
MODEL_NAME                = "paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME           = "vet_advice"
HIGH_CONFIDENCE_THRESHOLD = 0.65   # Similarité cosinus forte
LOW_CONFIDENCE_THRESHOLD  = 0.45   # Similarité cosinus faible (avertissement)

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
# AGENT RAG SÉMANTIQUE — ChromaDB
# ──────────────────────────────────────────────────────────────────
class SemanticRAGAgent:
    """
    Agent RAG utilisant ChromaDB pour la recherche sémantique persistante.
    Les embeddings sont calculés une seule fois et sauvegardés sur disque.
    Supporte nativement EN, FR, AR et 47 autres langues.
    """

    def __init__(self, kb_path: Optional[str] = None):
        self.kb = []

        base_dir = Path(__file__).resolve().parent.parent
        if kb_path is None:
            kb_path = base_dir / "data" / "vet_advice_kb.json"
        self.kb_path = Path(kb_path)

        self._chroma_dir = base_dir / "data" / "chroma_db"
        self._ef = SentenceTransformerEmbeddingFunction(model_name=MODEL_NAME)
        self._client, self._collection = self._init_chroma()

        self._load_kb()
        self._populate_collection()

    def _init_chroma(self):
        """Initialise ChromaDB — recrée le répertoire si la base est corrompue."""
        import shutil
        for attempt in range(2):
            try:
                self._chroma_dir.mkdir(parents=True, exist_ok=True)
                client = chromadb.PersistentClient(path=str(self._chroma_dir))
                collection = client.get_or_create_collection(
                    name               = COLLECTION_NAME,
                    embedding_function = self._ef,
                    metadata           = {"hnsw:space": "cosine"},
                )
                collection.count()  # force DB access to detect corruption early
                return client, collection
            except Exception as exc:
                if attempt == 0:
                    logger.warning(f"[RAGAgent] ChromaDB corrompue — réinitialisation ({exc})")
                    try:
                        shutil.rmtree(str(self._chroma_dir), ignore_errors=True)
                    except Exception:
                        pass
                else:
                    logger.error(f"[RAGAgent] ChromaDB irrécupérable : {exc}")
                    raise

    def _load_kb(self):
        try:
            with open(self.kb_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.kb = data.get('scenarios', [])
            logger.info(f"KB chargée : {len(self.kb)} scénarios")
        except Exception as e:
            logger.error(f"Erreur chargement KB : {e}")
            self.kb = []

    def _populate_collection(self):
        """Peuple ChromaDB — repopule automatiquement si la KB a grandi."""
        if not self.kb:
            return
        current_count = self._collection.count()
        if current_count >= len(self.kb):
            logger.info(f"Collection ChromaDB à jour ({current_count} docs) — skip encodage.")
            return
        if current_count > 0:
            logger.info(f"KB mise à jour ({current_count} → {len(self.kb)} docs) — repopulation ChromaDB.")
            self._client.delete_collection(COLLECTION_NAME)
            self._collection = self._client.get_or_create_collection(
                name               = COLLECTION_NAME,
                embedding_function = self._ef,
                metadata           = {"hnsw:space": "cosine"},
            )

        ids, documents, metadatas = [], [], []
        for scenario in self.kb:
            doc = " ".join([
                scenario.get('title_fr', ''),
                scenario.get('title_en', ''),
                " ".join(scenario.get('trigger_symptoms', [])),
                " ".join(scenario.get('trigger_keywords', [])),
                " ".join(scenario.get('species', [])),
                scenario.get('advice', '')[:100],
            ])
            ids.append(scenario.get('id', f"sc_{len(ids)}"))
            documents.append(doc)
            metadatas.append({
                "urgency"     : scenario.get('urgency', 'LOW'),
                "species"     : ",".join(scenario.get('species', [])),
                "is_emergency": str(scenario.get('urgency', 'LOW') in ['HIGH', 'CRITICAL']),
            })

        logger.info(f"Encodage et indexation de {len(ids)} scénarios dans ChromaDB...")
        self._collection.add(ids=ids, documents=documents, metadatas=metadatas)
        logger.info("Collection ChromaDB peuplée et persistée sur disque.")

    def _build_fallback(self) -> AdviceResult:
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
               top_k: int = 5) -> AdviceResult:
        """
        Cherche le scénario le plus pertinent via ChromaDB (HNSW cosinus).

        ChromaDB retourne des distances cosinus [0, 2].
        Similarité = 1 - distance  (1.0 = identique, 0.0 = opposé).
        """
        if self._collection.count() == 0:
            logger.warning("Collection ChromaDB vide → fallback")
            return self._build_fallback()

        n = min(top_k, self._collection.count())
        results = self._collection.query(
            query_texts = [query],
            n_results   = n,
            include     = ["metadatas", "distances", "documents"],
        )

        ids       = results["ids"][0]
        distances = results["distances"][0]
        metas     = results["metadatas"][0]

        # Construire un index rapide id→scenario
        kb_index = {s.get('id', ''): s for s in self.kb}

        for chroma_id, distance, meta in zip(ids, distances, metas):
            similarity = 1.0 - distance   # cosinus : distance = 1 - sim
            scenario   = kb_index.get(chroma_id)
            if scenario is None:
                continue

            # Filtre espèce
            if species:
                species_list = [s.lower() for s in scenario.get('species', [])]
                if species.lower() not in species_list:
                    continue

            # Vérifier exclusions
            exclusions = scenario.get('exclusion_keywords', [])
            if any(e.lower() in query.lower() for e in exclusions):
                continue

            # Seuil minimum
            if similarity < LOW_CONFIDENCE_THRESHOLD:
                logger.info(f"Score trop faible : {round(similarity, 2)} → fallback")
                return self._build_fallback()

            match_quality = "high" if similarity >= HIGH_CONFIDENCE_THRESHOLD else "low"
            advice = scenario.get('advice', '')
            if match_quality == "low":
                advice += LOW_CONFIDENCE_WARNING

            logger.info(f"Match ChromaDB : {chroma_id} (sim={round(similarity, 2)}, qualité={match_quality})")

            return AdviceResult(
                scenario_id     = chroma_id,
                title           = scenario.get('title_fr', scenario.get('title_en', '')),
                advice          = advice,
                home_care       = scenario.get('home_care', []),
                watch_for       = scenario.get('watch_for', []),
                when_to_consult = scenario.get('when_to_consult', ''),
                preparation     = scenario.get('preparation_for_vet', []),
                urgency         = scenario.get('urgency', 'LOW'),
                confidence      = similarity,
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
_CONTEXT_RAG_PROMPT = """Agent KB de DoctoAgent. Récupère les données vétérinaires pour les symptômes détectés.

Par symptôme : get_possible_causes + get_symptom_info + get_red_flags + get_home_care + get_evolution_timeline
Par espèce : get_species_vulnerabilities
Si HIGH/CRITICAL : get_first_aid_steps | Si intoxication : get_toxic_foods

JSON uniquement :
{"symptoms_data":{"<sym>":{"causes":[],"red_flags":[],"home_care":[],"timeline":{},"info":{}}},"species_info":{"vulnerabilities":[],"vaccination":{}},"first_aid":{},"breed_risks":{}}"""


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

            def _build_prompt(self, ctx):
                symptom_ctx = ctx.get("_symptom_context", {})
                urgency_ctx = ctx.get("_urgency_context", {})
                return (
                    f"Symptômes:{symptom_ctx.get('symptoms_normalized',[])} | "
                    f"Animal:{symptom_ctx.get('animal','?')} | "
                    f"Urgence:{urgency_ctx.get('refined_level','LOW')}\n"
                    f"Appelle les outils KB pour chaque symptôme puis retourne le JSON."
                )

            def run(self, ctx):
                # Reset du cache et des données collectées avant chaque run
                self._call_cache:    set  = set()
                self._collected: dict = {
                    "symptoms_data": {},
                    "species_info" : {},
                    "first_aid"    : {},
                    "toxic_foods"  : {},
                    "breed_risks"  : {},
                }
                result = super().run(ctx)
                # Si le JSON final est tronqué/invalide (fallback),
                # utiliser les données collectées pendant l'exécution des outils
                if (not result or result.get("status") == "fallback") \
                        and self._collected.get("symptoms_data"):
                    logger.info("[ContextRAGAgent] JSON tronqué → données tool calls utilisées")
                    return self._collected
                return result

            def _execute_tool_calls(self, tool_calls: list):
                from langchain_core.messages import ToolMessage
                results = []
                for tc in tool_calls:
                    name = tc.get("name", "")
                    args = tc.get("args", {})
                    key  = (name, str(sorted(args.items())))
                    if key in self._call_cache:
                        results.append(ToolMessage(
                            content=f"[CACHE] '{name}' déjà appelé.",
                            tool_call_id=tc.get("id", name),
                        ))
                        continue
                    self._call_cache.add(key)
                    tool_results = super()._execute_tool_calls([tc])
                    # Collecter le résultat dans la structure Python directement
                    if tool_results:
                        content = tool_results[0].content
                        sym = args.get("symptom_key", "")
                        sd  = self._collected["symptoms_data"]
                        if name == "get_possible_causes" and sym:
                            sd.setdefault(sym, {})["causes"]    = content
                        elif name == "get_symptom_info" and sym:
                            sd.setdefault(sym, {})["info"]      = content
                        elif name == "get_red_flags" and sym:
                            sd.setdefault(sym, {})["red_flags"] = content
                        elif name == "get_home_care" and sym:
                            sd.setdefault(sym, {})["home_care"] = content
                        elif name == "get_evolution_timeline" and sym:
                            sd.setdefault(sym, {})["timeline"]  = content
                        elif name == "get_species_vulnerabilities":
                            self._collected["species_info"]["vulnerabilities"] = content
                        elif name == "get_first_aid_steps":
                            etype = args.get("emergency_type", "general")
                            self._collected["first_aid"][etype] = content
                        elif name == "get_toxic_foods":
                            self._collected["toxic_foods"] = content
                    results.extend(tool_results)
                return results

            def _parse_output(self, raw, ctx):
                # Préférer les données collectées (pas de risque de troncature)
                if self._collected.get("symptoms_data"):
                    return self._collected
                return super()._parse_output(raw, ctx)

            def _fallback(self, ctx, error=""):
                return {"symptoms_data": {}, "species_info": {}, "first_aid": {}, "breed_risks": {}}

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

    rag_agent = SemanticRAGAgent()

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
