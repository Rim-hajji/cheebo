"""
DoctoAgent - Train v2 : NLTK + VetBERT
=======================================

Pipeline :
  1. NLTK    → prétraitement (tokenisation, stopwords, lemmatisation)
  2. VetBERT → classification urgence + intent
     (fallback : distilbert-base-uncased si VetBERT indisponible)

NER : géré séparément dans train_ner_vetbert.py

Anti-leakage : split AVANT augmentation, val/test jamais touchés.

Usage :
  py train_all_models_v2.py --fast --task urgency
  py train_all_models_v2.py --fast --task intent
  py train_all_models_v2.py --fast --task all
  py train_all_models_v2.py --task urgency        # full quality (lent)
"""

import argparse
import json
import random
import re
from collections import Counter
from pathlib import Path

import nltk
import numpy as np
import torch
from datasets import Dataset
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
)
from sklearn.model_selection import StratifiedShuffleSplit
from tqdm import tqdm
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)
from transformers.trainer_callback import EarlyStoppingCallback

# ──────────────────────────────────────────────────────────────────
# NLTK — Téléchargement ressources
# ──────────────────────────────────────────────────────────────────
print("Téléchargement ressources NLTK...")
for resource in ["punkt", "punkt_tab", "stopwords", "wordnet", "averaged_perceptron_tagger"]:
    nltk.download(resource, quiet=True)

# ──────────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────────
MODEL_NAME   = "havocy28/VetBERT"
FAST_MODEL   = "havocy28/VetBERT"
MAX_LENGTH   = 128
FAST_MAX_LEN = 64
SEED         = 42
NUM_EPOCHS   = 10
FAST_EPOCHS  = 5
FAST_BATCH   = 32

LABEL_SMOOTHING  = 0.1
MAX_CLASS_WEIGHT = 5.0

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

# ──────────────────────────────────────────────────────────────────
# PATHS
# ──────────────────────────────────────────────────────────────────
DATA_DIR   = Path("../../dataset_builder/data_real")
OUTPUT_DIR = Path("./models_v2")
OUTPUT_DIR.mkdir(exist_ok=True)

_balanced    = DATA_DIR / "doctoagent_balanced.json"
_clean       = DATA_DIR / "doctoagent_clean.json"
DATASET_PATH = _balanced if _balanced.exists() else _clean
print(f"  Dataset  : {'[ÉQUILIBRÉ] ' if _balanced.exists() else '[ORIGINAL] '}{DATASET_PATH.name}")

# Suppléments d'entraînement (exemples additionnels à merger)
SUPPLEMENT_PATH   = DATA_DIR / "doctoagent_train_supplement.json"
SUPPLEMENT_V2_PATH = DATA_DIR / "doctoagent_train_supplement_v2.json"
# Test set indépendant (jamais vu à l'entraînement)
BACKEND_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EXT_TEST_PATH    = BACKEND_DATA_DIR / "independent_test_set.json"

# ──────────────────────────────────────────────────────────────────
# LABELS
# ──────────────────────────────────────────────────────────────────
URGENCY_LABELS = {0: "LOW", 1: "MODERATE", 2: "HIGH", 3: "CRITICAL"}
URGENCY_STR2ID = {v: k for k, v in URGENCY_LABELS.items()}

INTENT_LABELS = {
    0: "describe_symptom",
    1: "ask_advice",
    2: "emergency",
    3: "follow_up",
}

tokenizer = None  # initialisé dans main()


# ══════════════════════════════════════════════════════════════════
# ÉTAPE 1 — NLTK : PRÉTRAITEMENT
# ══════════════════════════════════════════════════════════════════
class NLTKPreprocessor:
    """
    Prétraitement NLP avec NLTK :
      - Tokenisation (word_tokenize)
      - Suppression stopwords (EN)
      - Lemmatisation (WordNetLemmatizer)
      - Nettoyage ponctuation
    """

    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words("english"))
        self.medical_keep = {
            "not", "no", "never", "can't", "cannot", "won't",
            "bleeding", "blood", "pain", "severe", "urgent",
        }
        self.stop_words -= self.medical_keep
        print(f"  NLTK Preprocessor initialisé ({len(self.stop_words)} stopwords)")

    def preprocess(self, text: str) -> str:
        # 1. Nettoyage basique
        text = text.strip()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"http\S+", "", text)

        # 2. Tokenisation NLTK
        tokens = word_tokenize(text.lower())

        # 3. Lemmatisation + suppression stopwords
        processed = []
        for token in tokens:
            if token.isalpha():
                lemma = self.lemmatizer.lemmatize(token)
                processed.append(lemma)

        processed_text = " ".join(processed)

        # Texte hybride : original + lemmatisé
        return f"{text} {processed_text}"

    def get_tokens(self, text: str) -> list:
        tokens = word_tokenize(text.lower())
        return [
            self.lemmatizer.lemmatize(t)
            for t in tokens
            if t.isalpha() and t not in self.stop_words
        ]

    def preprocess_dataset(self, data: list) -> list:
        print(f"  Prétraitement NLTK de {len(data)} exemples...")
        processed = []
        for item in tqdm(data, desc="NLTK preprocessing"):
            new_item = item.copy()
            new_item["text"] = self.preprocess(item["text"])
            processed.append(new_item)
        return processed


# Singleton NLTK preprocessor
nltk_preprocessor = NLTKPreprocessor()


# ══════════════════════════════════════════════════════════════════
# CHARGEMENT DATASET
# ══════════════════════════════════════════════════════════════════
def load_dataset_clean():
    """Charge le dataset principal + supplément, retourne (intent_data, urgency_data)."""
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset introuvable : {DATASET_PATH}\n"
            f"Vérifiez que DATA_DIR pointe vers le bon dossier."
        )

    print(f"  Chargement : {DATASET_PATH}")
    raw = json.loads(DATASET_PATH.read_text(encoding="utf-8"))

    # Merger les suppléments d'entraînement si disponibles
    for sup_path in [SUPPLEMENT_PATH, SUPPLEMENT_V2_PATH]:
        if sup_path.exists():
            sup = json.loads(sup_path.read_text(encoding="utf-8"))
            print(f"  Supplément : {sup_path.name} ({len(sup)} records)")
            raw = raw + sup
        else:
            print(f"  [info] Supplément non trouvé : {sup_path.name}")

    intent_data  = []
    urgency_data = []

    for s in raw:
        text = s.get("text", "").strip()
        if not text:
            continue
        intent = s.get("intent")
        urg    = s.get("urgency", "MODERATE")

        if intent is not None:
            intent_data.append({"text": text, "label": int(intent)})
        if urg in URGENCY_STR2ID:
            urgency_data.append({"text": text, "label": URGENCY_STR2ID[urg]})

    # Stats
    print(f"\n  Dataset total (principal + supplément) : {len(raw)} records")

    urg_c = Counter(d["label"] for d in urgency_data)
    print("  Urgence :")
    for uid, uname in URGENCY_LABELS.items():
        c = urg_c.get(uid, 0)
        print(f"    {uname:<10} : {c:>5} ({c/max(len(urgency_data),1)*100:.1f}%)")

    int_c = Counter(d["label"] for d in intent_data)
    print("  Intent :")
    for iid, iname in INTENT_LABELS.items():
        c = int_c.get(iid, 0)
        print(f"    {iname:<20} : {c:>5} ({c/max(len(intent_data),1)*100:.1f}%)")

    return intent_data, urgency_data


# ══════════════════════════════════════════════════════════════════
# MÉTRIQUES
# ══════════════════════════════════════════════════════════════════
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    p, r, f1, _ = precision_recall_fscore_support(
        labels, preds, average="macro", zero_division=0
    )
    return {"f1": f1, "precision": p, "recall": r}


# ══════════════════════════════════════════════════════════════════
# WEIGHTED LOSS TRAINER
# ══════════════════════════════════════════════════════════════════
class WeightedTrainer(Trainer):
    def __init__(self, *args, class_weights=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.class_weights = class_weights

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels  = inputs.pop("labels")
        outputs = model(**inputs)
        loss = torch.nn.CrossEntropyLoss(
            weight          = self.class_weights.to(outputs.logits.device),
            label_smoothing = LABEL_SMOOTHING,
        )(outputs.logits, labels)
        return (loss, outputs) if return_outputs else loss


def compute_class_weights(labels, n_classes):
    counts  = Counter(labels)
    total   = len(labels)

    if counts:
        max_c = max(counts.values())
        min_c = min(counts.values())
        ratio = max_c / max(min_c, 1)
        if ratio > 10:
            print(f"  [⚠️  DÉSÉQUILIBRE SÉVÈRE] Ratio {ratio:.1f}x — class weights actifs")
        elif ratio > 3:
            print(f"  [⚠️  Déséquilibre modéré] Ratio {ratio:.1f}x")
        else:
            print(f"  [✅ Équilibré] Ratio {ratio:.1f}x")
        for i in range(n_classes):
            c    = counts.get(i, 0)
            name = INTENT_LABELS.get(i, URGENCY_LABELS.get(i, str(i)))
            print(f"    classe {i} ({name:<20}): {c:>5} exemples")

    weights = [total / (n_classes * counts.get(i, 1)) for i in range(n_classes)]
    mean_w  = sum(weights) / len(weights)
    weights = [min(w / mean_w, MAX_CLASS_WEIGHT) for w in weights]
    return torch.tensor(weights, dtype=torch.float)


# ══════════════════════════════════════════════════════════════════
# SPLIT STRATIFIÉ (anti-leakage)
# ══════════════════════════════════════════════════════════════════
def _hash(text: str) -> str:
    import hashlib
    return hashlib.md5(text.lower().strip().encode()).hexdigest()


def stratified_split(data, val_ratio=0.10, test_ratio=0.10):
    """Split stratifié AVANT toute augmentation."""
    labels    = [d["label"] for d in data]
    idx       = list(range(len(data)))
    counts    = Counter(labels)
    min_count = min(counts.values())

    if min_count < 3:
        print(f"  [⚠️] Classe trop petite ({min_count} ex.) → split aléatoire")
        random.shuffle(idx)
        n  = len(idx)
        t1 = int(n * (1 - val_ratio - test_ratio))
        t2 = int(n * (1 - test_ratio))
        train_i, val_i, test_i = idx[:t1], idx[t1:t2], idx[t2:]
    else:
        try:
            sss1 = StratifiedShuffleSplit(n_splits=1, test_size=test_ratio, random_state=SEED)
            train_val_i, test_i = next(sss1.split(idx, labels))
            tv_labels = [labels[i] for i in train_val_i]
            val_adj   = val_ratio / (1 - test_ratio)
            sss2 = StratifiedShuffleSplit(n_splits=1, test_size=val_adj, random_state=SEED)
            sub_train, sub_val = next(sss2.split(list(range(len(train_val_i))), tv_labels))
            train_i = [train_val_i[i] for i in sub_train]
            val_i   = [train_val_i[i] for i in sub_val]
        except ValueError as e:
            print(f"  [⚠️] Stratified split échoué ({e}) → split aléatoire")
            random.shuffle(idx)
            n  = len(idx)
            t1 = int(n * (1 - val_ratio - test_ratio))
            t2 = int(n * (1 - test_ratio))
            train_i, val_i, test_i = idx[:t1], idx[t1:t2], idx[t2:]

    train_labels = [data[i]["label"] for i in train_i]
    print(f"  Split train distribution : {dict(Counter(train_labels))}")

    return (
        [data[i] for i in train_i],
        [data[i] for i in val_i],
        [data[i] for i in list(test_i)],
    )


# ══════════════════════════════════════════════════════════════════
# AUGMENTATION DE DONNÉES (train uniquement — anti-leakage)
# ══════════════════════════════════════════════════════════════════

# Table de synonymes vétérinaires FR
_VET_SYNONYMS: dict[str, list[str]] = {
    # animaux
    "chien":          ["chien", "toutou", "canidé", "chiot"],
    "chat":           ["chat", "félin", "minou", "chaton"],
    "lapin":          ["lapin", "lapereau", "lapin nain"],
    "hamster":        ["hamster", "petit rongeur"],
    "perroquet":      ["perroquet", "psittacidé", "oiseau"],
    "furet":          ["furet", "mustélidé"],
    "oiseau":         ["oiseau", "volatile"],
    "tortue":         ["tortue", "reptile"],
    "cheval":         ["cheval", "équidé", "jument", "poney"],
    "cochon d'inde":  ["cochon d'inde", "cobaye"],
    "rat":            ["rat", "rongeur"],
    # symptômes
    "vomit":          ["vomit", "régurgite", "rend"],
    "diarrhée":       ["diarrhée", "selles molles", "colite"],
    "tousse":         ["tousse", "a une toux", "est enrhumé"],
    "éternue":        ["éternue", "a des éternuements"],
    "boite":          ["boite", "claudique", "marche mal", "boitille"],
    "saigne":         ["saigne", "perd du sang", "hémorragie"],
    "convulse":       ["convulse", "a des convulsions", "tremble violemment"],
    "inconscient":    ["inconscient", "sans connaissance", "ne répond pas"],
    "paralysé":       ["paralysé", "ne peut plus bouger", "immobile"],
    "ne mange plus":  ["ne mange plus", "refuse de manger", "n'a plus d'appétit"],
    "gratte":         ["se gratte", "se démange", "a des démangeaisons"],
    "perd ses poils": ["perd ses poils", "a de l'alopécie", "perd sa fourrure"],
    # modificateurs
    "beaucoup":       ["beaucoup", "énormément", "fréquemment"],
    "depuis":         ["depuis", "cela fait", "ça fait"],
    "grave":          ["grave", "sérieux", "sévère", "inquiétant"],
}

_FR_PREFIXES = [
    "", "", "",
    "Bonjour, ",
    "Bonsoir, ",
    "Salut, ",
    "Bonjour à tous, ",
    "Aidez-moi svp, ",
    "Question urgente : ",
    "Bonsoir docteur, ",
    "S'il vous plaît, ",
    "Bonjour docteur, ",
]

_FR_SUFFIXES = [
    "",
    " Que faire ?",
    " Est-ce normal ?",
    " Dois-je aller chez le vétérinaire ?",
    " Avez-vous des conseils ?",
    " C'est grave ?",
    " Que conseillez-vous ?",
    " Merci d'avance.",
]

_PARAPHRASE_RULES: list[tuple[str, str]] = [
    ("mon {a} ne mange plus",   "depuis quelque temps, mon {a} refuse toute nourriture"),
    ("mon {a} vomit",           "mon {a} a des vomissements"),
    ("mon {a} a la diarrhée",   "mon {a} souffre de diarrhée"),
    ("mon {a} se gratte",       "mon {a} présente des démangeaisons"),
    ("mon {a} tousse",          "mon {a} a une toux persistante"),
    ("mon {a} boite",           "mon {a} présente une boiterie"),
    ("mon {a} perd ses poils",  "mon {a} a de l'alopécie"),
    ("mon {a} est inconscient", "mon {a} ne répond plus et semble inconscient"),
    ("mon {a} convulse",        "mon {a} a des crises convulsives"),
    ("mon {a} saigne",          "mon {a} présente un saignement"),
    ("mon {a} ne boit plus",    "mon {a} a arrêté de s'hydrater"),
    ("mon {a} tremble",         "mon {a} présente des tremblements"),
]

_ANIMALS_FR = [
    "chien", "chat", "lapin", "hamster", "perroquet", "furet",
    "oiseau", "tortue", "cheval", "cochon d'inde", "rat", "reptile",
    "chienne", "chatte",
]

# Substitutions style SMS / informel
_INFORMAL_SUBS = [
    ("s'il vous plaît", "svp"),
    ("s'il te plaît",   "stp"),
    ("vétérinaire",     "véto"),
    ("beaucoup",        "bcp"),
    ("toujours",        "tjrs"),
    ("depuis quelques", "depuis qques"),
    ("parce que",       "pcq"),
    ("peut-être",       "p-e"),
]


def _apply_synonyms_fr(text: str, n_swaps: int = 1) -> str:
    result = text
    lower  = result.lower()
    swapped = 0
    keys = list(_VET_SYNONYMS.keys())
    random.shuffle(keys)
    for key in keys:
        if swapped >= n_swaps:
            break
        if key in lower:
            candidates = [s for s in _VET_SYNONYMS[key] if s.lower() != key.lower()]
            if not candidates:
                continue
            replacement = random.choice(candidates)
            idx = lower.find(key)
            if idx >= 0:
                result  = result[:idx] + replacement + result[idx + len(key):]
                lower   = result.lower()
                swapped += 1
    return result


def _add_framing_fr(text: str) -> str:
    prefix = random.choice(_FR_PREFIXES)
    suffix = random.choice(_FR_SUFFIXES)
    r = text.strip()
    non_empty = [p.strip(", ").lower() for p in _FR_PREFIXES if p]
    if prefix and not any(r.lower().startswith(p) for p in non_empty):
        r = prefix + r[0].lower() + r[1:]
    if suffix and not r.endswith("?") and not r.endswith("."):
        r = r.rstrip(".!") + suffix
    return r


def _paraphrase_fr(text: str) -> str | None:
    t = text.lower()
    for pattern, tmpl in _PARAPHRASE_RULES:
        for a in _ANIMALS_FR:
            if pattern.replace("{a}", a) in t:
                new_text = tmpl.replace("{a}", a)
                return new_text[0].upper() + new_text[1:]
    return None


def _simulate_informal_fr(text: str) -> str:
    result = text
    for formal, informal in _INFORMAL_SUBS:
        if formal in result.lower():
            idx    = result.lower().find(formal)
            result = result[:idx] + informal + result[idx + len(formal):]
            break
    return result


def augment_train_split(train_data: list, target_per_class: int = 1500) -> list:
    """Augmente UNIQUEMENT les données d'entraînement. Val/test jamais touchés."""
    import hashlib

    def _h(t: str) -> str:
        return hashlib.md5(t.lower().strip().encode()).hexdigest()

    label_counts = Counter(d["label"] for d in train_data)
    n_classes    = len(label_counts)
    target_total = target_per_class * n_classes
    max_count    = max(label_counts.values())

    seen   = {_h(d["text"]) for d in train_data}
    result = list(train_data)

    weights = {lbl: max_count / cnt for lbl, cnt in label_counts.items()}
    pool    = [(d, weights[d["label"]]) for d in train_data]

    strategies = ["synonym_fr", "framing_fr", "paraphrase_fr", "informal_fr", "combined_fr"]
    attempts = 0
    while len(result) < target_total and attempts < target_total * 20:
        attempts += 1
        items_pool, wts = zip(*pool)
        (orig,) = random.choices(items_pool, weights=wts, k=1)
        text = orig["text"]

        strategy = random.choice(strategies)
        if strategy == "synonym_fr":
            new_text = _apply_synonyms_fr(text, n_swaps=random.randint(1, 2))
        elif strategy == "framing_fr":
            new_text = _add_framing_fr(text)
        elif strategy == "paraphrase_fr":
            p = _paraphrase_fr(text)
            new_text = p if p else _add_framing_fr(text)
        elif strategy == "informal_fr":
            new_text = _simulate_informal_fr(text)
        else:  # combined_fr
            new_text = _apply_synonyms_fr(_add_framing_fr(text), n_swaps=1)

        if new_text == text:
            continue
        h = _h(new_text)
        if h in seen:
            continue
        seen.add(h)
        result.append({**orig, "text": new_text})

    random.shuffle(result)
    print(f"  Augmentation train : {len(train_data)} → {len(result)} (+{len(result)-len(train_data)})")
    dist = dict(Counter(d["label"] for d in result))
    print(f"  Distribution après aug : {dict(sorted(dist.items()))}")
    return result


# ══════════════════════════════════════════════════════════════════
# TOKENISATION
# ══════════════════════════════════════════════════════════════════
def tokenize_dataset(ds: Dataset) -> Dataset:
    return ds.map(
        lambda ex: tokenizer(
            ex["text"],
            padding    = "max_length",
            truncation = True,
            max_length = MAX_LENGTH,
        ),
        batched=True,
    )


# ══════════════════════════════════════════════════════════════════
# ÉVALUATION SUR TEST SET EXTERNE INDÉPENDANT
# ══════════════════════════════════════════════════════════════════

def evaluate_independent_test(trainer, task_name: str, labels_dict: dict, ext_test_path: Path) -> None:
    """Évalue le modèle sur un fichier de test totalement indépendant."""
    if not ext_test_path.exists():
        print(f"\n  [⚠️] Test indépendant introuvable : {ext_test_path}")
        return

    print(f"\n  {'='*55}")
    print(f"  ÉVALUATION TEST INDÉPENDANT : {ext_test_path.name}")
    print(f"  {'='*55}")

    raw = json.loads(ext_test_path.read_text(encoding="utf-8"))
    ext_data = []
    for item in raw:
        text = item.get("text", "").strip()
        if not text:
            continue
        if task_name.lower() == "intent":
            lbl = item.get("intent")
            if lbl is not None:
                ext_data.append({"text": nltk_preprocessor.preprocess(text), "label": int(lbl)})
        elif task_name.lower() == "urgency":
            urg = item.get("urgency", "")
            if urg in URGENCY_STR2ID:
                ext_data.append({"text": nltk_preprocessor.preprocess(text), "label": URGENCY_STR2ID[urg]})

    if not ext_data:
        print(f"  [⚠️] Aucun exemple valide pour '{task_name}' dans {ext_test_path.name}")
        return

    label_names = [labels_dict[i] for i in range(len(labels_dict))]
    dist        = {labels_dict[k]: v for k, v in Counter(d["label"] for d in ext_data).items()}
    print(f"  Exemples : {len(ext_data)} | Distribution : {dist}")

    ext_ds    = tokenize_dataset(Dataset.from_list(ext_data))
    raw_preds = trainer.predict(ext_ds)
    y_pred    = np.argmax(raw_preds.predictions, axis=1)
    y_true    = raw_preds.label_ids

    p, r, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
    print(f"\n  [TEST INDÉPENDANT] Macro F1={f1:.4f}  Precision={p:.4f}  Recall={r:.4f}")
    print(classification_report(y_true, y_pred, target_names=label_names, zero_division=0))
    print("  Matrice de confusion :")
    print(confusion_matrix(y_true, y_pred))

    # Sauvegarde des métriques externes
    out_dir = OUTPUT_DIR / f"results_{task_name.lower()}"
    out_dir.mkdir(parents=True, exist_ok=True)
    ext_metrics = {
        "source"          : str(ext_test_path),
        "n_samples"       : len(ext_data),
        "macro_f1"        : float(f1),
        "macro_precision" : float(p),
        "macro_recall"    : float(r),
        "per_class"       : classification_report(
            y_true, y_pred, target_names=label_names, zero_division=0, output_dict=True
        ),
    }
    ext_out = out_dir / "independent_test_metrics.json"
    ext_out.write_text(json.dumps(ext_metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Métriques sauvegardées : {ext_out}")


# ══════════════════════════════════════════════════════════════════
# ENTRAÎNEMENT CLASSIFIER (Urgency + Intent)
# ══════════════════════════════════════════════════════════════════
def train_classifier(task_name, labels_dict, data, use_aug: bool = False, ext_test_path: Path = None):
    print(f"\n{'='*60}")
    print(f"  TRAINING : {task_name}")
    print(f"  Modèle   : {MODEL_NAME}")
    print(f"  Augment  : {use_aug}")
    print(f"{'='*60}")
    print(f"  Dataset  : {len(data)} samples")
    print(f"  Dist.    : {dict(Counter(d['label'] for d in data))}")

    # ── Étape 1 : NLTK preprocessing ────────────────────────────
    print("\n  [NLTK] Prétraitement du texte...")
    data_nltk = nltk_preprocessor.preprocess_dataset(data)

    # ── Étape 2 : Split ─────────────────────────────────────────
    train_data, val_data, test_data = stratified_split(data_nltk)
    print(f"  Split    : train={len(train_data)} val={len(val_data)} test={len(test_data)}")

    # ── Vérification anti-leakage ────────────────────────────────
    test_hashes = {_hash(d["text"]) for d in test_data}
    leakage     = {_hash(d["text"]) for d in train_data} & test_hashes
    if leakage:
        print(f"  [WARN] {len(leakage)} leaks supprimés du train")
        train_data = [d for d in train_data if _hash(d["text"]) not in test_hashes]

    # ── Étape 2b : Augmentation train (optionnelle) ──────────────
    if use_aug:
        print("\n  [AUG] Augmentation des données d'entraînement...")
        train_data = augment_train_split(train_data, target_per_class=1500)

    # ── Étape 3 : Tokenisation ───────────────────────────────────
    print(f"\n  [HuggingFace] Tokenisation avec {MODEL_NAME}...")
    train_ds = tokenize_dataset(Dataset.from_list(train_data))
    val_ds   = tokenize_dataset(Dataset.from_list(val_data))
    test_ds  = tokenize_dataset(Dataset.from_list(test_data))

    # ── Étape 4 : Chargement VetBERT ────────────────────────────
    print(f"\n  [VetBERT] Chargement du modèle...")
    try:
        model = AutoModelForSequenceClassification.from_pretrained(
            MODEL_NAME,
            num_labels              = len(labels_dict),
            id2label                = labels_dict,
            label2id                = {v: k for k, v in labels_dict.items()},
            ignore_mismatched_sizes = True,
        )
        print(f"  VetBERT chargé avec succès !")
    except Exception as e:
        print(f"  VetBERT indisponible ({e}) → fallback distilbert-base-uncased")
        model = AutoModelForSequenceClassification.from_pretrained(
            "distilbert-base-uncased",
            num_labels = len(labels_dict),
            id2label   = labels_dict,
            label2id   = {v: k for k, v in labels_dict.items()},
        )

    # ── Étape 5 : Class weights ──────────────────────────────────
    cw = compute_class_weights([d["label"] for d in train_data], len(labels_dict))
    print(f"  Class weights : {[round(w, 3) for w in cw.tolist()]}")

    # ── Étape 6 : Training arguments ────────────────────────────
    output_dir = OUTPUT_DIR / f"results_{task_name.lower()}"
    final_dir  = OUTPUT_DIR / f"{task_name.lower()}_model"
    output_dir.mkdir(parents=True, exist_ok=True)

    fast_mode  = (NUM_EPOCHS == FAST_EPOCHS)
    batch_size = FAST_BATCH if fast_mode else 16
    grad_acc   = 1 if fast_mode else 2

    steps_per_epoch = max(1, len(train_data) // (batch_size * grad_acc))
    warmup_steps    = max(10, int(steps_per_epoch * NUM_EPOCHS * 0.1))

    training_args = TrainingArguments(
        output_dir                  = str(output_dir),
        learning_rate               = 2e-5,
        warmup_steps                = warmup_steps,
        per_device_train_batch_size = batch_size,
        per_device_eval_batch_size  = batch_size * 2,
        num_train_epochs            = NUM_EPOCHS,
        weight_decay                = 0.05,
        eval_strategy               = "epoch",
        save_strategy               = "epoch",
        load_best_model_at_end      = True,
        metric_for_best_model       = "f1",
        greater_is_better           = True,
        logging_steps               = 20,
        seed                        = SEED,
        use_cpu                     = True,
        gradient_accumulation_steps = grad_acc,
        save_total_limit            = 2,
        report_to                   = "none",
    )

    # ── Étape 7 : Entraînement ───────────────────────────────────
    trainer = WeightedTrainer(
        model            = model,
        args             = training_args,
        train_dataset    = train_ds,
        eval_dataset     = val_ds,
        processing_class = tokenizer,
        compute_metrics  = compute_metrics,
        class_weights    = cw,
        callbacks        = [EarlyStoppingCallback(
            early_stopping_patience  = 3,
            early_stopping_threshold = 0.005,
        )],
    )

    print(f"\n  Démarrage de l'entraînement...")
    trainer.train()

    # ── Étape 8 : Évaluation ─────────────────────────────────────
    print(f"\n  --- Évaluation test set ({task_name}) ---")
    raw_preds   = trainer.predict(test_ds)
    y_pred      = np.argmax(raw_preds.predictions, axis=1)
    y_true      = raw_preds.label_ids
    label_names = [labels_dict[i] for i in range(len(labels_dict))]

    p, r, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    print(f"\n  Macro F1={f1:.4f}  Precision={p:.4f}  Recall={r:.4f}")
    print(classification_report(y_true, y_pred, target_names=label_names, zero_division=0))
    print("  Matrice de confusion :")
    print(confusion_matrix(y_true, y_pred))

    # ── Sauvegarde métriques ─────────────────────────────────────
    metrics = {
        "task"          : task_name,
        "model"         : MODEL_NAME,
        "preprocessing" : "NLTK (tokenize + lemmatize + stopwords) + HuggingFace tokenizer",
        "test_macro_f1" : float(f1),
        "test_precision": float(p),
        "test_recall"   : float(r),
        "n_train"       : len(train_data),
        "n_val"         : len(val_data),
        "n_test"        : len(test_data),
        "per_class"     : classification_report(
            y_true, y_pred,
            target_names  = label_names,
            zero_division = 0,
            output_dict   = True,
        ),
    }
    metrics_path = output_dir / "test_metrics.json"
    metrics_path.write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\n  Métriques sauvegardées : {metrics_path}")

    # ── Sauvegarde modèle ────────────────────────────────────────
    trainer.save_model(str(final_dir))
    tokenizer.save_pretrained(str(final_dir))
    print(f"  Modèle sauvegardé    : {final_dir}")

    # ── Étape 9 : Évaluation sur test indépendant (si fourni) ────
    if ext_test_path is not None:
        evaluate_independent_test(trainer, task_name, labels_dict, ext_test_path)


# ══════════════════════════════════════════════════════════════════
# ENTRY POINT
# ══════════════════════════════════════════════════════════════════
def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--fast", action="store_true",
                   help="Fast mode : max_len=64 + 5 epochs")
    p.add_argument("--task",
                   choices=["intent", "urgency", "all"],
                   default="all")
    p.add_argument("--use-aug", action="store_true",
                   help="Augmenter les données d'entraînement (synonymes FR, reformulation, style SMS)")
    p.add_argument("--ext-test", type=str, default=None,
                   help="Chemin vers un fichier de test indépendant (défaut : independent_test_set.json si trouvé)")
    return p.parse_args()


def main():
    global MODEL_NAME, MAX_LENGTH, NUM_EPOCHS, tokenizer

    args = parse_args()

    if args.fast:
        MODEL_NAME = FAST_MODEL
        MAX_LENGTH = FAST_MAX_LEN
        NUM_EPOCHS = FAST_EPOCHS

    # Résoudre le chemin du test indépendant
    if args.ext_test:
        ext_test = Path(args.ext_test)
    elif EXT_TEST_PATH.exists():
        ext_test = EXT_TEST_PATH
    else:
        ext_test = None

    use_aug = args.use_aug

    print(f"\n{'='*60}")
    print("  DOCTOAGENT v2 — NLTK + VetBERT (Urgency + Intent)")
    print(f"  Modèle      : {MODEL_NAME}")
    print(f"  Max length  : {MAX_LENGTH} tokens")
    print(f"  Epochs      : {NUM_EPOCHS}")
    print(f"  Task        : {args.task}")
    print(f"  Mode        : {'FAST (~1-2h CPU)' if args.fast else 'FULL (~8-10h CPU)'}")
    print(f"  Augmentation: {'OUI' if use_aug else 'NON'}")
    print(f"  Test indép. : {ext_test.name if ext_test else 'NON'}")
    print(f"  NER         : utiliser train_ner_vetbert.py séparément")
    print(f"{'='*60}\n")

    # ── Charger dataset ──────────────────────────────────────────
    intent_data, urgency_data = load_dataset_clean()

    # ── Charger tokenizer ────────────────────────────────────────
    print(f"\nChargement tokenizer {MODEL_NAME}...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        print("Tokenizer VetBERT chargé !")
    except Exception as e:
        print(f"VetBERT tokenizer indisponible ({e}) → fallback distilbert-base-uncased")
        tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

    # ── Entraînement ─────────────────────────────────────────────
    if args.task in ("urgency", "all"):
        train_classifier("Urgency", URGENCY_LABELS, urgency_data, use_aug=use_aug, ext_test_path=ext_test)

    if args.task in ("intent", "all"):
        train_classifier("Intent", INTENT_LABELS, intent_data, use_aug=use_aug, ext_test_path=ext_test)

    print(f"\n{'='*60}")
    print("  ENTRAÎNEMENT TERMINÉ !")
    print(f"  Modèles sauvegardés dans : {OUTPUT_DIR}/")
    print(f"  Pour NER → py train_ner_vetbert.py")
    print(f"{'='*60}")

    # ── Résumé final ─────────────────────────────────────────────
    print("\n  Résumé des modèles :")
    for model_dir in OUTPUT_DIR.glob("*_model"):
        metrics_file = OUTPUT_DIR / f"results_{model_dir.name.replace('_model','')}" / "test_metrics.json"
        if metrics_file.exists():
            m = json.loads(metrics_file.read_text())
            print(f"  {model_dir.name:<20} : F1 = {m.get('test_macro_f1', 0):.4f}")


if __name__ == "__main__":
    main()