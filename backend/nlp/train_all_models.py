"""
DoctoAgent - Train Intent + Urgency classifiers + spaCy NER
===========================================================

Model      : havocy28/VetBERT  (pre-trained on 15M real veterinary records)
Fast mode  : distilbert-base-uncased (6x faster on CPU)
Dataset    : data_real/doctoagent_clean.json

Anti-leakage guarantee
----------------------
Split FIRST on base data, THEN augment only the training portion.
Val and test sets always stay original and unaugmented.

Usage:
  py train_all_models.py --fast --use-aug --task urgency   # recommended on CPU
  py train_all_models.py --fast --use-aug --task intent
  py train_all_models.py --fast --use-aug --task ner
  py train_all_models.py --fast --use-aug --task all
  py train_all_models.py --use-aug --task urgency          # full quality (slow)
"""

import argparse
import json
import os
import random
import subprocess
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import spacy
import torch
from datasets import Dataset
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import StratifiedShuffleSplit
from spacy.tokens import DocBin
from tqdm import tqdm
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
)
from transformers.trainer_callback import EarlyStoppingCallback

# ──────────────────────────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────────────────────────
MODEL_NAME = "havocy28/VetBERT"          # Pre-trained on 15M veterinary records
FAST_MODEL = "distilbert-base-uncased"   # Fast fallback for CPU
MAX_LENGTH = 128
FAST_MAX_LEN = 64
SEED       = 42
NUM_EPOCHS = 10
FAST_EPOCHS = 5
FAST_BATCH  = 32

LABEL_SMOOTHING  = 0.1
MAX_CLASS_WEIGHT = 5.0

random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

# ──────────────────────────────────────────────────────────────────
# PATHS
# ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = Path("./models")
OUTPUT_DIR.mkdir(exist_ok=True)

DATASET_PATH = DATA_DIR / "doctoagent_clean.json"

# ──────────────────────────────────────────────────────────────────
# LABELS
# ──────────────────────────────────────────────────────────────────
INTENT_LABELS = {
    0: "describe_symptom",
    1: "ask_advice",
    2: "emergency",
    3: "follow_up",
}
URGENCY_LABELS = {
    0: "LOW",
    1: "MODERATE",
    2: "HIGH",
    3: "CRITICAL",
}
URGENCY_STR2ID = {v: k for k, v in URGENCY_LABELS.items()}

tokenizer = None  # initialised after args parsed


# ──────────────────────────────────────────────────────────────────
# DATASET LOADER
# ──────────────────────────────────────────────────────────────────
def load_dataset_clean():
    """
    Load doctoagent_clean.json and return (intent_data, urgency_data, ner_data).
    """
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATASET_PATH}")

    print(f"  Loading: {DATASET_PATH}")
    raw = json.loads(DATASET_PATH.read_text(encoding="utf-8"))

    intent_data  = []
    urgency_data = []
    ner_data     = []

    for s in raw:
        text = s.get("text", "").strip()
        if not text:
            continue

        intent = s.get("intent")
        urg    = s.get("urgency", "MODERATE")
        ents   = s.get("entities", [])

        if intent is not None:
            intent_data.append({"text": text, "label": int(intent)})

        if urg in URGENCY_STR2ID:
            urgency_data.append({"text": text, "label": URGENCY_STR2ID[urg]})

        if ents:
            ner_data.append({"text": text, "entities": ents})

    # Print distributions
    print(f"\n  Dataset loaded: {len(raw)} records")

    urg_counts = Counter(d["label"] for d in urgency_data)
    print("  Urgency distribution:")
    for uid, uname in URGENCY_LABELS.items():
        cnt = urg_counts.get(uid, 0)
        print(f"    {uname:<10}: {cnt:>5} ({cnt/len(urgency_data)*100:.1f}%)")

    int_counts = Counter(d["label"] for d in intent_data)
    print("  Intent distribution:")
    for iid, iname in INTENT_LABELS.items():
        cnt = int_counts.get(iid, 0)
        print(f"    {iname:<20}: {cnt:>5} ({cnt/len(intent_data)*100:.1f}%)")

    print(f"  NER records with entities: {len(ner_data)}")

    return intent_data, urgency_data, ner_data


# ──────────────────────────────────────────────────────────────────
# METRICS
# ──────────────────────────────────────────────────────────────────
def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    p, r, f1, _ = precision_recall_fscore_support(
        labels, preds, average="macro", zero_division=0
    )
    return {"f1": f1, "precision": p, "recall": r}


# ──────────────────────────────────────────────────────────────────
# WEIGHTED LOSS TRAINER
# ──────────────────────────────────────────────────────────────────
class WeightedTrainer(Trainer):
    def __init__(self, *args, class_weights=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.class_weights = class_weights

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        loss = torch.nn.CrossEntropyLoss(
            weight=self.class_weights,
            label_smoothing=LABEL_SMOOTHING,
        )(outputs.logits, labels)
        return (loss, outputs) if return_outputs else loss


def compute_class_weights(labels, n_classes):
    counts = Counter(labels)
    total  = len(labels)
    weights = [total / (n_classes * counts.get(i, 1)) for i in range(n_classes)]
    mean_w  = sum(weights) / len(weights)
    weights = [min(w / mean_w, MAX_CLASS_WEIGHT) for w in weights]
    return torch.tensor(weights, dtype=torch.float)


# ──────────────────────────────────────────────────────────────────
# SPLIT (anti-leakage)
# ──────────────────────────────────────────────────────────────────
def stratified_split(data, val_ratio=0.10, test_ratio=0.10):
    """
    Safe stratified split. Returns (train, val, test).
    Split is done BEFORE any augmentation.
    """
    labels = [d["label"] for d in data]
    idx    = list(range(len(data)))

    min_count = min(Counter(labels).values())

    if min_count < 3:
        random.shuffle(idx)
        n  = len(idx)
        t1 = int(n * (1 - val_ratio - test_ratio))
        t2 = int(n * (1 - test_ratio))
        train_i, val_i, test_i = idx[:t1], idx[t1:t2], idx[t2:]
    else:
        sss1 = StratifiedShuffleSplit(
            n_splits=1, test_size=test_ratio, random_state=SEED
        )
        train_val_i, test_i = next(sss1.split(idx, labels))
        tv_labels    = [labels[i] for i in train_val_i]
        val_adj      = val_ratio / (1 - test_ratio)
        sss2 = StratifiedShuffleSplit(
            n_splits=1, test_size=val_adj, random_state=SEED
        )
        sub_train, sub_val = next(
            sss2.split(list(range(len(train_val_i))), tv_labels)
        )
        train_i = [train_val_i[i] for i in sub_train]
        val_i   = [train_val_i[i] for i in sub_val]

    return (
        [data[i] for i in train_i],
        [data[i] for i in val_i],
        [data[i] for i in list(test_i)],
    )


# ──────────────────────────────────────────────────────────────────
# AUGMENTATION (train only)
# ──────────────────────────────────────────────────────────────────
def _norm(text):
    return " ".join(text.lower().strip().split())

def _hash(text):
    import hashlib
    return hashlib.md5(_norm(text).encode()).hexdigest()

PREFIXES = [
    "", "", "",
    "Help! ", "Urgent: ", "Please advise: ",
    "Hi everyone, ", "Hello, ",
]
SUFFIXES = [
    "", "", "",
    " What should I do?",
    " Is this serious?",
    " Should I go to the vet?",
    " Please help.",
    " Any advice?",
]

SYMPTOM_SYNONYMS = {
    "vomiting"    : ["vomiting", "throwing up", "being sick"],
    "diarrhea"    : ["diarrhea", "loose stools", "watery stools"],
    "lethargy"    : ["lethargy", "weakness", "tiredness", "being lethargic"],
    "not eating"  : ["not eating", "loss of appetite", "refusing food"],
    "coughing"    : ["coughing", "has a cough", "persistent cough"],
    "limping"     : ["limping", "lame", "difficulty walking"],
    "scratching"  : ["scratching", "itching", "pruritus"],
    "seizure"     : ["seizure", "convulsion", "fit"],
    "bleeding"    : ["bleeding", "hemorrhage", "blood loss"],
    "fever"       : ["fever", "high temperature", "pyrexia"],
}

def _apply_synonyms(text):
    result = text
    for key, synonyms in SYMPTOM_SYNONYMS.items():
        if key in result.lower():
            repl   = random.choice(synonyms)
            idx    = result.lower().find(key)
            result = result[:idx] + repl + result[idx + len(key):]
            break
    return result

def _add_framing(text):
    prefix = random.choice(PREFIXES)
    suffix = random.choice(SUFFIXES)
    r = text.strip()
    if prefix:
        r = prefix + r[0].lower() + r[1:]
    if suffix and not r.endswith("?"):
        r = r.rstrip(".!") + suffix
    return r

def augment_train_split(train_data, target_per_class=1500):
    """
    Augment ONLY the training split.
    Val and test are NEVER touched → zero leakage.
    """
    label_counts = Counter(d["label"] for d in train_data)
    n_classes    = len(label_counts)
    target_total = target_per_class * n_classes
    max_count    = max(label_counts.values())

    seen   = {_hash(d["text"]) for d in train_data}
    result = list(train_data)

    weights = {lbl: max_count / cnt for lbl, cnt in label_counts.items()}
    pool    = [(d, weights[d["label"]]) for d in train_data]

    attempts = 0
    while len(result) < target_total and attempts < target_total * 15:
        attempts += 1
        items_pool, wts = zip(*pool)
        (orig,) = random.choices(items_pool, weights=wts, k=1)
        text = orig["text"]

        strategy = random.choice(["synonym", "framing", "combined"])
        if strategy == "synonym":
            new_text = _apply_synonyms(text)
        elif strategy == "framing":
            new_text = _add_framing(text)
        else:
            new_text = _apply_synonyms(_add_framing(text))

        if new_text == text:
            continue
        h = _hash(new_text)
        if h in seen:
            continue
        seen.add(h)
        result.append({**orig, "text": new_text})

    random.shuffle(result)
    print(f"  Augmented train : {len(train_data)} -> {len(result)}")
    dist = dict(Counter(d["label"] for d in result))
    print(f"  Class dist after aug : {dist}")
    return result


# ──────────────────────────────────────────────────────────────────
# TOKENIZATION
# ──────────────────────────────────────────────────────────────────
def tokenize_dataset(ds):
    return ds.map(
        lambda ex: tokenizer(
            ex["text"],
            padding    = "max_length",
            truncation = True,
            max_length = MAX_LENGTH,
        ),
        batched=True,
    )


# ──────────────────────────────────────────────────────────────────
# CLASSIFIER TRAINING
# ──────────────────────────────────────────────────────────────────
def train_classifier(task_name, labels_dict, data, use_aug):
    print(f"\n{'='*60}")
    print(f"  TRAINING: {task_name}")
    print(f"  Model   : {MODEL_NAME}")
    print(f"  Augment : {use_aug}")
    print(f"{'='*60}")
    print(f"  Base dataset : {len(data)} samples")
    print(f"  Distribution : {dict(Counter(d['label'] for d in data))}")

    # Split BEFORE augmentation (anti-leakage)
    train_data, val_data, test_data = stratified_split(data)
    print(f"  Split : train={len(train_data)} val={len(val_data)} test={len(test_data)}")

    # Augment train only
    if use_aug:
        train_data = augment_train_split(train_data, target_per_class=1500)

    # Verify no leakage
    test_hashes  = {_hash(d["text"]) for d in test_data}
    train_hashes = {_hash(d["text"]) for d in train_data}
    leakage = test_hashes & train_hashes
    if leakage:
        print(f"  [WARN] Removing {len(leakage)} leaked samples from train")
        train_data = [d for d in train_data if _hash(d["text"]) not in test_hashes]

    # Tokenize
    train_ds = tokenize_dataset(Dataset.from_list(train_data))
    val_ds   = tokenize_dataset(Dataset.from_list(val_data))
    test_ds  = tokenize_dataset(Dataset.from_list(test_data))

    # Model
    print(f"\n  Loading {MODEL_NAME}...")
    try:
        model = AutoModelForSequenceClassification.from_pretrained(
            MODEL_NAME,
            num_labels = len(labels_dict),
            id2label   = labels_dict,
            label2id   = {v: k for k, v in labels_dict.items()},
            ignore_mismatched_sizes = True,
        )
        print(f"  Model loaded successfully !")
    except Exception as e:
        print(f"  VetBERT failed ({e}), falling back to distilbert-base-uncased")
        model = AutoModelForSequenceClassification.from_pretrained(
            "distilbert-base-uncased",
            num_labels = len(labels_dict),
            id2label   = labels_dict,
            label2id   = {v: k for k, v in labels_dict.items()},
        )

    # Class weights
    cw = compute_class_weights([d["label"] for d in train_data], len(labels_dict))
    print(f"  Class weights : {[round(w, 3) for w in cw.tolist()]}")

    # Output dirs
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

    print(f"\n  Starting training...")
    trainer.train()

    # Evaluate on test set
    print(f"\n  --- Test set evaluation ({task_name}) ---")
    raw_preds   = trainer.predict(test_ds)
    y_pred      = np.argmax(raw_preds.predictions, axis=1)
    y_true      = raw_preds.label_ids
    label_names = [labels_dict[i] for i in range(len(labels_dict))]

    p, r, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    print(f"\n  Macro F1={f1:.4f}  Precision={p:.4f}  Recall={r:.4f}")
    print(classification_report(y_true, y_pred, target_names=label_names, zero_division=0))
    print("  Confusion matrix:")
    print(confusion_matrix(y_true, y_pred))

    # Save metrics
    metrics = {
        "task"          : task_name,
        "model"         : MODEL_NAME,
        "test_macro_f1" : float(f1),
        "test_precision": float(p),
        "test_recall"   : float(r),
        "n_train"       : len(train_data),
        "n_val"         : len(val_data),
        "n_test"        : len(test_data),
        "per_class"     : classification_report(
            y_true, y_pred,
            target_names = label_names,
            zero_division = 0,
            output_dict  = True,
        ),
    }
    metrics_path = output_dir / "test_metrics.json"
    metrics_path.write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\n  Metrics saved  : {metrics_path}")

    # Save model
    trainer.save_model(str(final_dir))
    tokenizer.save_pretrained(str(final_dir))
    print(f"  Model saved    : {final_dir}")


# ──────────────────────────────────────────────────────────────────
# NER TRAINING (spaCy)
# ──────────────────────────────────────────────────────────────────
def remove_overlapping_entities(entities):
    if not entities:
        return []
    sorted_ents = sorted(entities, key=lambda x: -(x[1] - x[0]))
    cleaned = []
    for start, end, label in sorted_ents:
        if not any(not (end <= s or start >= e) for s, e, _ in cleaned):
            cleaned.append((start, end, label))
    return cleaned


def _build_spacy_bin(data, nlp, desc):
    db = DocBin()
    skipped = 0
    for item in tqdm(data, desc=desc):
        try:
            entities = remove_overlapping_entities(item.get("entities", []))
            doc = nlp.make_doc(item.get("text", ""))
            ents = []
            for start, end, label in entities:
                span = doc.char_span(start, end, label=label, alignment_mode="contract")
                if span is not None:
                    ents.append(span)
            doc.ents = ents
            db.add(doc)
        except Exception:
            skipped += 1
    return db, skipped


def train_ner(ner_data, use_aug):
    print(f"\n{'='*60}")
    print(f"  TRAINING: NER (spaCy)")
    print(f"  Samples : {len(ner_data)}")
    print(f"{'='*60}")

    random.shuffle(ner_data)
    n  = len(ner_data)
    t1 = int(n * 0.70)
    t2 = int(n * 0.85)

    train_data = ner_data[:t1]
    dev_data   = ner_data[t1:t2]
    test_data  = ner_data[t2:]

    print(f"  Split : train={len(train_data)} dev={len(dev_data)} test={len(test_data)}")

    nlp = spacy.blank("en")

    ner_dir = OUTPUT_DIR / "ner_model_spacy"
    ner_dir.mkdir(parents=True, exist_ok=True)

    train_db, sk_t = _build_spacy_bin(train_data, nlp, "NER train")
    dev_db,   sk_d = _build_spacy_bin(dev_data,   nlp, "NER dev")

    train_path = OUTPUT_DIR / "train.spacy"
    dev_path   = OUTPUT_DIR / "dev.spacy"
    train_db.to_disk(train_path)
    dev_db.to_disk(dev_path)
    print(f"  train.spacy (skipped {sk_t}), dev.spacy (skipped {sk_d})")

    config_path = OUTPUT_DIR / "config.cfg"
    subprocess.run([
        sys.executable, "-m", "spacy", "init", "config",
        str(config_path),
        "--lang", "en",
        "--pipeline", "tok2vec,ner",
        "--optimize", "efficiency",
        "--force",
    ], check=False)

    result = subprocess.run([
        sys.executable, "-m", "spacy", "train", str(config_path),
        "--output",          str(ner_dir),
        "--paths.train",     str(train_path),
        "--paths.dev",       str(dev_path),
        "--training.dropout",    "0.2",
        "--training.max_epochs", "30",
        "--training.patience",   "500",
        "--gpu-id", "-1",
    ], capture_output=False, text=True)

    status = "OK" if result.returncode == 0 else f"exit code {result.returncode}"
    print(f"  NER training: {status}")
    print(f"  NER model saved: {ner_dir}")


# ──────────────────────────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--use-aug",  action="store_true",
                   help="Augment training split only (val/test stay clean)")
    p.add_argument("--fast",     action="store_true",
                   help="Fast mode: distilbert + max_len=64 + 5 epochs")
    p.add_argument("--task",
                   choices=["intent", "urgency", "ner", "all"],
                   default="all")
    return p.parse_args()


def main():
    global MODEL_NAME, MAX_LENGTH, NUM_EPOCHS, tokenizer

    args = parse_args()

    if args.fast:
        MODEL_NAME = FAST_MODEL
        MAX_LENGTH = FAST_MAX_LEN
        NUM_EPOCHS = FAST_EPOCHS

    print(f"\n{'='*60}")
    print("  DOCTOAGENT - NLP TRAINING")
    print(f"  Model      : {MODEL_NAME}")
    print(f"  Max length : {MAX_LENGTH} tokens")
    print(f"  Epochs     : {NUM_EPOCHS}")
    print(f"  Augment    : {'TRAIN ONLY (val/test untouched)' if args.use_aug else 'disabled'}")
    print(f"  Task       : {args.task}")
    print(f"  Mode       : {'FAST (~1-2h CPU)' if args.fast else 'FULL (~8-10h CPU)'}")
    print(f"{'='*60}\n")

    # Load dataset
    intent_data, urgency_data, ner_data = load_dataset_clean()

    # Load tokenizer
    print(f"\nLoading tokenizer: {MODEL_NAME}...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
        print("Tokenizer loaded!")
    except Exception as e:
        print(f"VetBERT tokenizer failed ({e}), using distilbert...")
        tokenizer = AutoTokenizer.from_pretrained("distilbert-base-uncased")

    # Train selected tasks
    if args.task in ("urgency", "all"):
        train_classifier("Urgency", URGENCY_LABELS, urgency_data, args.use_aug)

    if args.task in ("intent", "all"):
        train_classifier("Intent", INTENT_LABELS, intent_data, args.use_aug)

    if args.task in ("ner", "all"):
        train_ner(ner_data, args.use_aug)

    print("\n" + "=" * 60)
    print("  TRAINING COMPLETE !")
    print(f"  Models saved in: {OUTPUT_DIR}/")
    print("=" * 60)


if __name__ == "__main__":
    main()