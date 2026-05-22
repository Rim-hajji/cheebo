"""
Evaluation modeles VetBERT v2 sur les vrais jeux de test.
  - Intent      : doctoagent_test_clean.json (180 samples)
  - Urgency     : doctoagent_test_clean.json (180 samples)
  - NER VetBERT : ner_bio_test.json (240 samples)

Usage :
  cd c:\\Users\\nesrin\\Desktop\\module_docto_agent
  py backend/nlp/eval_models_v2.py
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
from collections import defaultdict
from pathlib import Path

import torch
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from transformers import (
    AutoModelForSequenceClassification,
    AutoModelForTokenClassification,
    AutoTokenizer,
    pipeline as hf_pipeline,
)

BASE_DIR   = Path(__file__).resolve().parent.parent.parent
NLP_DIR    = Path(__file__).resolve().parent
MODELS_DIR = NLP_DIR / "models_v2"
DATA_DIR   = BASE_DIR / "dataset_builder" / "data_real"

TEST_CLF_PATH = DATA_DIR / "doctoagent_test_clean.json"
TEST_NER_PATH = DATA_DIR / "ner_bio_test.json"

INTENT_ID2LABEL  = {0: "describe_symptom", 1: "ask_advice", 2: "emergency", 3: "follow_up"}
URGENCY_ID2LABEL = {0: "LOW", 1: "MODERATE", 2: "HIGH", 3: "CRITICAL"}
URGENCY_LABEL2ID = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}


def sep(title=""):
    print("\n" + "=" * 62)
    if title:
        print(f"  {title}")
        print("=" * 62)


def load_clf_model(model_dir, task):
    if not model_dir.exists():
        print(f"  [SKIP] {task} - modele introuvable : {model_dir}")
        return None
    print(f"  Chargement {task} <- {model_dir.name} ...")
    try:
        clf = hf_pipeline(
            "text-classification",
            model=str(model_dir),
            tokenizer=str(model_dir),
            device=-1,
            truncation=True,
            max_length=128,
        )
        print(f"  [OK] {task} charge")
        return clf
    except Exception as e:
        print(f"  [ERREUR] {task} : {e}")
        return None


def eval_classification(clf, texts, true_ids, id2label, task_name):
    sep(f"EVALUATION -- {task_name}  ({len(texts)} samples)")
    label_names = [id2label[i] for i in sorted(id2label)]

    preds = []
    for text in texts:
        try:
            out = clf(text)[0]
            if isinstance(out, list):
                out = out[0]
            raw = out["label"]
            if raw.startswith("LABEL_"):
                pid = int(raw.split("_")[1])
            else:
                inv = {v: k for k, v in id2label.items()}
                pid = inv.get(raw, 0)
        except Exception:
            pid = 0
        preds.append(pid)

    print(classification_report(true_ids, preds, target_names=label_names, zero_division=0))
    macro = f1_score(true_ids, preds, average="macro", zero_division=0)
    print(f"  Macro F1       : {macro:.4f}")
    print(f"  Seuil rapport  : >= 0.70")
    print(f"  Statut         : {'PASS' if macro >= 0.70 else 'A AMELIORER'}")
    print("\n  Matrice de confusion :")
    cm = confusion_matrix(true_ids, preds)
    header = "               " + "  ".join(f"{n[:8]:>8}" for n in label_names)
    print(header)
    for i, row in enumerate(cm):
        print(f"  {label_names[i][:14]:<14} " + "  ".join(f"{v:>8}" for v in row))
    return macro


def bio_to_spans(tags):
    spans = []
    start = None
    cur_label = None
    for i, tag in enumerate(tags):
        if tag.startswith("B-"):
            if start is not None:
                spans.append((start, i, cur_label))
            start = i
            cur_label = tag[2:]
        elif tag.startswith("I-") and start is not None and tag[2:] == cur_label:
            pass
        else:
            if start is not None:
                spans.append((start, i, cur_label))
                start = None
                cur_label = None
    if start is not None:
        spans.append((start, len(tags), cur_label))
    return set(spans)


def eval_ner_vetbert():
    sep("EVALUATION -- NER VetBERT  (ner_bio_test.json)")

    ner_dir = MODELS_DIR / "ner_model_vetbert"
    if not ner_dir.exists():
        print(f"  [SKIP] NER model introuvable : {ner_dir}")
        return None

    if not TEST_NER_PATH.exists():
        print(f"  [SKIP] NER test set introuvable : {TEST_NER_PATH}")
        return None

    print(f"  Chargement NER <- {ner_dir.name} ...")
    tokenizer = AutoTokenizer.from_pretrained(str(ner_dir))
    model = AutoModelForTokenClassification.from_pretrained(
        str(ner_dir), torch_dtype=torch.float32
    )
    model.eval()
    id2label = model.config.id2label

    with open(TEST_NER_PATH, encoding="utf-8") as f:
        records = json.load(f)
    print(f"  {len(records)} sequences de test\n")

    stats = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})

    for rec in records:
        tokens    = rec["tokens"]
        true_tags = rec["ner_tags"]
        if not tokens:
            continue

        encoding = tokenizer(
            tokens,
            is_split_into_words=True,
            return_tensors="pt",
            truncation=True,
            max_length=128,
            padding=False,
        )

        with torch.no_grad():
            logits = model(**encoding).logits
        pred_ids = torch.argmax(logits, dim=2)[0].tolist()
        word_ids = encoding.word_ids()

        pred_tags = []
        seen = set()
        for idx, wid in enumerate(word_ids):
            if wid is None or wid in seen:
                continue
            seen.add(wid)
            pred_tags.append(id2label[pred_ids[idx]])
        while len(pred_tags) < len(tokens):
            pred_tags.append("O")
        pred_tags = pred_tags[:len(tokens)]

        true_spans = bio_to_spans(true_tags[:len(tokens)])
        pred_spans = bio_to_spans(pred_tags)

        for span in pred_spans:
            if span in true_spans:
                stats[span[2]]["tp"] += 1
            else:
                stats[span[2]]["fp"] += 1
        for span in true_spans:
            if span not in pred_spans:
                stats[span[2]]["fn"] += 1

    entity_labels = ["ANIMAL", "SYMPTOM", "BODY_PART", "DUREE"]
    print(f"  {'Label':<12} {'Precision':>10} {'Recall':>8} {'F1':>8} {'TP':>5} {'FP':>5} {'FN':>5}")
    print(f"  {'-'*57}")

    all_f1 = []
    total_tp = total_fp = total_fn = 0
    for lbl in entity_labels:
        tp = stats[lbl]["tp"]
        fp = stats[lbl]["fp"]
        fn = stats[lbl]["fn"]
        total_tp += tp; total_fp += fp; total_fn += fn
        p  = tp / (tp + fp) if (tp + fp) else 0.0
        r  = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * p * r / (p + r) if (p + r) else 0.0
        all_f1.append(f1)
        print(f"  {lbl:<12} {p:>10.4f} {r:>8.4f} {f1:>8.4f} {tp:>5} {fp:>5} {fn:>5}")

    mp = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0.0
    mr = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0.0
    mf = 2 * mp * mr / (mp + mr) if (mp + mr) else 0.0
    macro_f1 = sum(all_f1) / len(all_f1) if all_f1 else 0.0

    print(f"  {'-'*57}")
    print(f"  {'MICRO AVG':<12} {mp:>10.4f} {mr:>8.4f} {mf:>8.4f}")
    print(f"  {'MACRO AVG':<12} {'':>10} {'':>8} {macro_f1:>8.4f}")
    print(f"\n  Micro F1 (test reel)   : {mf:.4f}")
    print(f"  Macro F1 (test reel)   : {macro_f1:.4f}")
    print(f"  Seuil rapport          : >= 0.70")
    print(f"  Statut Micro           : {'PASS' if mf >= 0.70 else 'A AMELIORER'}")

    return mf, macro_f1


def main():
    sep("EVALUATION MODELES NLP v2 -- VetBERT")
    print(f"  Dossier modeles : {MODELS_DIR}")
    print(f"  Test CLF        : {TEST_CLF_PATH.name}  (existe={TEST_CLF_PATH.exists()})")
    print(f"  Test NER        : {TEST_NER_PATH.name}  (existe={TEST_NER_PATH.exists()})")

    if not TEST_CLF_PATH.exists():
        print(f"\n[ERREUR] Fichier test introuvable : {TEST_CLF_PATH}")
        sys.exit(1)

    with open(TEST_CLF_PATH, encoding="utf-8") as f:
        clf_data = json.load(f)
    print(f"\n  {len(clf_data)} samples charges pour Intent & Urgency")

    texts       = [s["text"] for s in clf_data]
    intent_ids  = [int(s["intent"]) for s in clf_data]
    urgency_ids = [URGENCY_LABEL2ID[s["urgency"]] for s in clf_data]

    results = {}

    intent_clf = load_clf_model(MODELS_DIR / "intent_model", "Intent VetBERT")
    if intent_clf:
        results["intent_macro_f1"] = eval_classification(
            intent_clf, texts, intent_ids, INTENT_ID2LABEL, "INTENT VetBERT"
        )

    urgency_clf = load_clf_model(MODELS_DIR / "urgency_model", "Urgency VetBERT")
    if urgency_clf:
        results["urgency_macro_f1"] = eval_classification(
            urgency_clf, texts, urgency_ids, URGENCY_ID2LABEL, "URGENCY VetBERT"
        )

    ner_result = eval_ner_vetbert()
    if ner_result:
        results["ner_micro_f1"], results["ner_macro_f1"] = ner_result

    sep("RESUME FINAL -- Metriques pour le rapport")
    print(f"  {'Modele':<28} {'Macro F1':>10}  {'Statut'}")
    print(f"  {'-'*58}")
    for key, val in results.items():
        name   = key.replace("_", " ").upper()
        status = "PASS" if val >= 0.70 else "A AMELIORER"
        print(f"  {name:<28} {val:>10.4f}  {status}")

    print("\n  (scores obtenus sur les vrais jeux de test)")
    sep()


if __name__ == "__main__":
    main()
