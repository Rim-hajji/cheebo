import logging
import json
import re
import warnings
from pathlib import Path
from typing import List, Dict, Any

import torch
import numpy as np
from pydantic import BaseModel
from transformers import (
    pipeline,
    AutoTokenizer,
    AutoModelForTokenClassification,
)

warnings.filterwarnings('ignore', message='.*Some weights.*')

# ──────────────────────────────────────────────────────────────────
# LOGGING
# ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────────
class NLPConfig:

    INTENT_CONFIDENCE_THRESHOLD  = 0.5
    URGENCY_CONFIDENCE_THRESHOLD = 0.5
    RAG_SIMILARITY_THRESHOLD     = 0.3

    # Mots-clés critiques (EN + FR uniquement)
    CRITICAL_KEYWORDS = [
        # FR
        "urgent", "urgence", "blessé", "saigne", "sang", "hémorragie",
        "respire plus", "au secours", "inconscient", "paralysé",
        "convulse", "grave", "empoisonné", "avale du poison",
        # EN
        "emergency", "wounded", "unconscious", "seizure", "convuls",
        "poison", "collapse", "bleeding", "dying", "not breathing",
        "can't breathe", "bloat", "hit by car", "critical", "severe",
        "paralyz", "help urgent", "rush to vet",
    ]

    NON_CRITICAL_PATTERNS = [
        "swollen paw", "scratching", "limping occasionally",
        "vomiting once", "sneezing", "cannot fly", "fell from",
        "licking", "itching", "hair loss", "bad breath",
        "not eating once", "sleeping more", "drinking more",
    ]

    # Patterns MODERATE — symptômes persistants qui méritent surveillance
    MODERATE_KEYWORDS = [
        # FR — durée + symptôme
        "ne mange plus", "ne mange pas", "mange moins", "perd l'appétit",
        "perte d'appétit", "refuse de manger", "ne boit plus", "ne boit pas",
        "léthargique", "léthargie", "apathique", "apathie", "abattu",
        "dort beaucoup", "dort tout le temps", "moins actif", "pas d'énergie",
        "yeux qui coulent", "yeux larmoyants", "écoulement", "larmoie",
        "vomit depuis", "vomissements depuis", "diarrhée depuis",
        "tousse depuis", "gratte depuis", "boite depuis",
        "depuis 2 jour", "depuis 3 jour", "depuis plusieurs jours",
        "depuis hier", "depuis 48", "depuis 24",
        "plusieurs fois", "à répétition", "régulièrement",
        # EN — persistent symptoms
        "not eating for", "hasn't eaten", "won't eat for",
        "lethargic", "lethargic since", "very tired", "no energy",
        "watery eyes", "eye discharge", "runny nose",
        "vomiting since", "vomiting for", "diarrhea since",
        "coughing since", "limping since",
        "for 2 day", "for 3 day", "for several days",
        "since yesterday", "since 2", "since 3",
        "multiple times", "repeatedly",
    ]


# ──────────────────────────────────────────────────────────────────
# RESULT MODEL
# ──────────────────────────────────────────────────────────────────
class NLPResult(BaseModel):
    original_text       : str
    language            : str
    tokens              : List[str]
    intent              : str
    intent_confidence   : float = 0.0
    urgency_score       : int
    urgency_label       : str
    urgency_confidence  : float = 0.0
    entities            : List[Dict[str, Any]]
    ner_source          : str   = "vetbert"


# ──────────────────────────────────────────────────────────────────
# PIPELINE
# ──────────────────────────────────────────────────────────────────
class NLPPipeline:

    def __init__(self, config: NLPConfig = None):
        self.config = config or NLPConfig()
        logger.info("Initialisation Pipeline DoctoAgent (100% VetBERT)...")

        self._nlp_dir = Path(__file__).resolve().parent

        # ── 1. VetBERT Intent ─────────────────────────────────────
        self.intent_path  = self._find_model_path("intent_model")
        self.classifier   = None

        if self.intent_path:
            try:
                self.classifier = pipeline(
                    "text-classification",
                    model = str(self.intent_path),
                    top_k = 1,
                )
                logger.info("VetBERT Intent chargé : " + str(self.intent_path))
            except Exception as e:
                logger.error("VetBERT Intent erreur : " + str(e))

        # ── 2. VetBERT Urgency ────────────────────────────────────
        self.urgency_path  = self._find_model_path("urgency_model")
        self.urgency_model = None

        if self.urgency_path:
            try:
                self.urgency_model = pipeline(
                    "text-classification",
                    model = str(self.urgency_path),
                    top_k = 1,
                )
                logger.info("VetBERT Urgency chargé : " + str(self.urgency_path))
            except Exception as e:
                logger.error("VetBERT Urgency erreur : " + str(e))

        # ── 3. VetBERT NER ────────────────────────────────────────
        self.ner_vetbert_tokenizer = None
        self.ner_vetbert_model     = None
        self.ner_vetbert_id2label  = None

        vetbert_ner_path = self._nlp_dir / "models_v2" / "ner_model_vetbert"
        if vetbert_ner_path.exists():
            try:
                self.ner_vetbert_tokenizer = AutoTokenizer.from_pretrained(
                    str(vetbert_ner_path)
                )
                self.ner_vetbert_model = AutoModelForTokenClassification.from_pretrained(
                    str(vetbert_ner_path),
                    torch_dtype = torch.float16,
                )
                self.ner_vetbert_model.eval()
                self.ner_vetbert_id2label = self.ner_vetbert_model.config.id2label
                logger.info("VetBERT NER chargé (float16) : " + str(vetbert_ner_path))
            except Exception as e:
                logger.error("VetBERT NER erreur : " + str(e))

        # ── 4. KB ─────────────────────────────────────────────────
        self.kb_data = {}
        kb_path = self._nlp_dir.parent / "data" / "symptom_kb.json"
        if kb_path.exists():
            try:
                with open(kb_path, "r", encoding="utf-8") as f:
                    self.kb_data = json.load(f)
                logger.info("KB chargé : " + str(len(self.kb_data)) + " symptômes")
            except Exception as e:
                logger.warning("KB erreur : " + str(e))


    # ─────────────────────────────────────────────
    # Helper
    # ─────────────────────────────────────────────
    def _find_model_path(self, model_name: str) -> Path | None:
        candidates = [
            self._nlp_dir / "models_v2" / model_name,
            self._nlp_dir / "models"    / model_name,
            self._nlp_dir / model_name,
        ]
        for p in candidates:
            if p.exists() and (p / "config.json").exists():
                return p
        return None

    # ─────────────────────────────────────────────
    # Détection de langue (heuristique légère)
    # ─────────────────────────────────────────────
    _FR_MARKERS = [
        "je ", "mon ", "ma ", "mes ", "le ", "la ", "les ", "est ",
        "sont ", "c'est", "votre ", "il ", "elle ", "ils ", "elles ",
        "depuis ", "depuis", "ne ", "n'", "pas ", "très ", "aussi ",
        "mais ", "avec ", "pour ", "dans ", "sur ", "qui ", "que ",
        "mon chat", "mon chien", "ma chatte", "mon lapin",
    ]

    def _detect_language(self, text: str) -> str:
        arabic = sum(1 for c in text if '؀' <= c <= 'ۿ')
        if arabic > len(text) * 0.15:
            return "ar"
        t = text.lower()
        fr_score = sum(1 for m in self._FR_MARKERS if m in t)
        return "fr" if fr_score >= 2 else "en"

    # ─────────────────────────────────────────────
    # Tokenisation (VetBERT tokenizer-compatible)
    # ─────────────────────────────────────────────
    def preprocess_text(self, text: str) -> List[str]:
        return text.split()

    # ─────────────────────────────────────────────
    # VetBERT NER
    # ─────────────────────────────────────────────
    def extract_entities(self, text: str) -> tuple[List[Dict[str, Any]], str]:
        if self.ner_vetbert_model is None:
            return [], "none"

        tokens = text.split()
        if not tokens:
            return [], "vetbert"

        encoding = self.ner_vetbert_tokenizer(
            tokens,
            is_split_into_words = True,
            return_tensors      = 'pt',
            truncation          = True,
            max_length          = 64,
        )

        with torch.no_grad():
            outputs = self.ner_vetbert_model(**encoding)

        predictions = torch.argmax(outputs.logits, dim=2)[0]
        word_ids    = encoding.word_ids()

        entities  = []
        prev_word = None
        current   = None

        for i, word_id in enumerate(word_ids):
            if word_id is None or word_id == prev_word:
                continue
            label = self.ner_vetbert_id2label[predictions[i].item()]
            token = tokens[word_id] if word_id < len(tokens) else ''

            if label.startswith('B-'):
                if current:
                    entities.append(current)
                current = {
                    'text': token, 'label': label[2:],
                    'start': 0, 'end': 0, 'confidence': 0.9,
                }
            elif label.startswith('I-') and current:
                current['text'] += ' ' + token
            else:
                if current:
                    entities.append(current)
                    current = None
            prev_word = word_id

        if current:
            entities.append(current)

        return entities, "vetbert"

    # ─────────────────────────────────────────────
    # Mappings
    # ─────────────────────────────────────────────
    URGENCY_LABEL_MAP = {
        "LOW": "LOW", "MODERATE": "MODERATE",
        "HIGH": "HIGH", "CRITICAL": "CRITICAL",
        "LABEL_0": "LOW", "LABEL_1": "MODERATE",
        "LABEL_2": "HIGH", "LABEL_3": "CRITICAL",
    }

    INTENT_LABEL_MAP = {
        "describe_symptom": "describe_symptom",
        "ask_advice": "ask_advice",
        "emergency": "emergency",
        "follow_up": "follow_up",
        "LABEL_0": "describe_symptom",
        "LABEL_1": "ask_advice",
        "LABEL_2": "emergency",
        "LABEL_3": "follow_up",
    }

    # ─────────────────────────────────────────────
    # PROCESS PRINCIPAL
    # ─────────────────────────────────────────────
    def process(self, text: str) -> NLPResult:
        logger.info("Analyse : " + text[:60] + "...")

        # ── 1. Langue ────────────────────────────────────────────
        language = self._detect_language(text)

        # ── 2. Tokenisation ──────────────────────────────────────
        tokens = self.preprocess_text(text)

        # ── 3. Intent (VetBERT) ──────────────────────────────────
        intent            = "describe_symptom"
        intent_confidence = 0.0

        if self.classifier:
            try:
                res = self.classifier(text)[0]
                if isinstance(res, list):
                    res = res[0]
                raw_label         = res.get("label", "LABEL_0")
                intent_confidence = float(res.get("score", 0.0))
                if intent_confidence >= self.config.INTENT_CONFIDENCE_THRESHOLD:
                    intent = self.INTENT_LABEL_MAP.get(raw_label, "describe_symptom")
            except Exception as e:
                logger.error("Intent erreur : " + str(e))

        # ── 4. Urgence (VetBERT) ─────────────────────────────────
        urg_label      = "LOW"
        urg_confidence = 0.0
        score          = 1

        if self.urgency_model:
            try:
                urg_res = self.urgency_model(text)[0]
                if isinstance(urg_res, list):
                    urg_res = urg_res[0]
                raw_urg        = urg_res.get("label", "LABEL_0")
                urg_confidence = float(urg_res.get("score", 0.0))
                urg_label      = self.URGENCY_LABEL_MAP.get(raw_urg, "LOW")
                mapping        = {"LOW": 1, "MODERATE": 4, "HIGH": 7, "CRITICAL": 10}
                score          = mapping.get(urg_label, 1)
            except Exception as e:
                logger.error("Urgency erreur : " + str(e))

        # ── 5. Override sécurité (mots-clés critiques) ───────────
        text_lower = text.lower()

        if any(kw in text_lower for kw in self.config.CRITICAL_KEYWORDS):
            logger.warning("Mot-clé critique détecté → override sécurité")
            if score < 7:
                urg_label = "HIGH"
                score     = 7
            if intent != "emergency":
                intent = "emergency"

        # ── 6. Override MODERATE — symptômes persistants ─────────
        if urg_label == "LOW":
            if any(kw in text_lower for kw in self.config.MODERATE_KEYWORDS):
                logger.info("Pattern MODERATE détecté → override LOW → MODERATE")
                urg_label = "MODERATE"
                score     = 4

        # ── 7. Anti-overcorrection ───────────────────────────────
        if urg_label == "CRITICAL":
            if any(p in text_lower for p in self.config.NON_CRITICAL_PATTERNS):
                logger.info("Anti-overcorrection : CRITICAL → HIGH")
                urg_label = "HIGH"
                score     = 7

        # ── 8. Entités (VetBERT NER) ─────────────────────────────
        entities, ner_source = self.extract_entities(text)

        return NLPResult(
            original_text      = text,
            language           = language,
            tokens             = tokens,
            intent             = intent,
            intent_confidence  = intent_confidence,
            urgency_score      = score,
            urgency_label      = urg_label,
            urgency_confidence = urg_confidence,
            entities           = entities,
            ner_source         = ner_source,
        )


# ──────────────────────────────────────────────────────────────────
# SINGLETON
# ──────────────────────────────────────────────────────────────────
nlp_pipeline = NLPPipeline()

if __name__ == "__main__":
    tests = [
        "My dog has been vomiting since yesterday",
        "Mon chat tousse depuis 2 jours",
        "My cat is so happy and playing",
        "My dog is bleeding and not breathing, emergency",
    ]
    for t in tests:
        res = nlp_pipeline.process(t)
        print("\n" + "=" * 50)
        print("Original   : " + res.original_text)
        print("Intent     : " + res.intent + " (" + str(round(res.intent_confidence, 2)) + ")")
        print("Urgency    : " + res.urgency_label + " (" + str(res.urgency_score) + "/10)")
        print("Entities   : " + str([(e['text'], e['label']) for e in res.entities]))
