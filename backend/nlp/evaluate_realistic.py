"""
Evaluate intent, urgency AND NER models on realistic hand-crafted test sets.

Gives TRUE scores reflecting real-world performance.
Synthetic val F1 (~0.99) is NOT a reliable indicator.

Usage:
  py backend/nlp/evaluate_realistic.py
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import spacy
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from transformers import pipeline as hf_pipeline

BASE_DIR  = Path(__file__).parent.parent
TEST_PATH     = BASE_DIR / "data" / "realistic_test_set.json"
NER_TEST_PATH = BASE_DIR / "data" / "realistic_ner_test.json"
NLP_DIR   = Path(__file__).parent

INTENT_LABELS  = {0: "INFO", 1: "CONSEIL", 2: "URGENCE", 3: "SUIVI"}
URGENCY_LABELS = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}
URGENCY_ID2L   = {0: "LOW", 1: "MODERATE", 2: "HIGH", 3: "CRITICAL"}


def load_model(model_dir: Path, task: str):
    if not model_dir.exists():
        print(f"  [skip] {task} model not found at {model_dir}")
        return None
    try:
        clf = hf_pipeline(
            "text-classification",
            model=str(model_dir),
            tokenizer=str(model_dir),
            device=-1,
        )
        print(f"  [ok] {task} model loaded from {model_dir}")
        return clf
    except Exception as e:
        print(f"  [error] could not load {task} model: {e}")
        return None


def evaluate(clf, samples, true_labels, id2label, task_name):
    print(f"\n{'='*55}")
    print(f"  REALISTIC EVALUATION — {task_name}")
    print(f"  {len(samples)} hand-crafted real-world examples")
    print(f"{'='*55}")

    preds = []
    for text in samples:
        try:
            out   = clf(text, truncation=True, max_length=128)[0]
            label = out["label"]
            # HuggingFace may return "LABEL_0" or the actual label name
            if label.startswith("LABEL_"):
                pred_id = int(label.split("_")[1])
            else:
                inv = {v: k for k, v in id2label.items()}
                pred_id = inv.get(label, 0)
            preds.append(pred_id)
        except Exception:
            preds.append(0)

    label_names = [id2label[i] for i in range(len(id2label))]
    print(classification_report(true_labels, preds, target_names=label_names, zero_division=0))

    from sklearn.metrics import f1_score
    macro_f1 = f1_score(true_labels, preds, average="macro", zero_division=0)
    print(f"  Macro F1 (realistic): {macro_f1:.4f}")
    print(f"  Target               : >= 0.70")
    print(f"  Status               : {'PASS' if macro_f1 >= 0.70 else 'NEEDS IMPROVEMENT'}")

    print("\n  Confusion matrix:")
    print(confusion_matrix(true_labels, preds))

    return macro_f1


def main():
    if not TEST_PATH.exists():
        print(f"[error] Test set not found: {TEST_PATH}")
        sys.exit(1)

    samples = json.loads(TEST_PATH.read_text(encoding="utf-8"))
    print(f"Loaded {len(samples)} realistic test examples\n")

    # ── Intent ──
    intent_clf = load_model(NLP_DIR / "intent_model", "Intent")
    if intent_clf:
        intent_texts  = [s["text"] for s in samples]
        intent_labels = [s["intent"] for s in samples]
        evaluate(intent_clf, intent_texts, intent_labels, INTENT_LABELS, "INTENT")

    # ── Urgency ──
    urgency_clf = load_model(NLP_DIR / "urgency_model", "Urgency")
    if urgency_clf:
        urgency_texts  = [s["text"] for s in samples]
        urgency_labels = [URGENCY_LABELS[s["urgency"]] for s in samples]
        evaluate(urgency_clf, urgency_texts, urgency_labels, URGENCY_ID2L, "URGENCY")

    # ── NER ──
    evaluate_ner(NLP_DIR / "ner_model_spacy" / "model-best")

    print("\n=== EVALUATION COMPLETE ===")
    print("Note: these scores reflect real-world performance.")
    print("Synthetic val F1 (~0.99) is NOT a reliable indicator.")


# ── NER evaluation ─────────────────────────────────────────────────────────────

def evaluate_ner(model_path: Path):
    print(f"\n{'='*55}")
    print("  REALISTIC EVALUATION — NER")
    print(f"{'='*55}")

    if not model_path.exists():
        print(f"  [skip] NER model not found at {model_path}")
        return

    if not NER_TEST_PATH.exists():
        print(f"  [skip] NER test set not found at {NER_TEST_PATH}")
        return

    nlp = spacy.load(str(model_path))
    samples = json.loads(NER_TEST_PATH.read_text(encoding="utf-8"))
    print(f"  {len(samples)} hand-crafted NER examples")

    # entity-level TP / FP / FN per label
    stats = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})

    errors = []
    for sample in samples:
        text     = sample["text"]
        expected = {(e[0].lower(), e[1]) for e in sample["entities"]}

        doc = nlp(text)
        predicted = {(e.text.lower(), e.label_) for e in doc.ents}

        for pair in expected:
            lbl = pair[1]
            if pair in predicted:
                stats[lbl]["tp"] += 1
            else:
                stats[lbl]["fn"] += 1
                errors.append(f"  MISSED  [{lbl}] '{pair[0]}' in: {text!r}")

        for pair in predicted:
            lbl = pair[1]
            if pair not in expected:
                stats[lbl]["fp"] += 1
                errors.append(f"  WRONG   [{lbl}] '{pair[0]}' in: {text!r}")

    all_labels = sorted(stats.keys())
    total_tp = total_fp = total_fn = 0

    print(f"\n  {'Label':<12} {'Precision':>10} {'Recall':>8} {'F1':>8} {'TP':>5} {'FP':>5} {'FN':>5}")
    print(f"  {'-'*56}")

    for lbl in all_labels:
        tp = stats[lbl]["tp"]
        fp = stats[lbl]["fp"]
        fn = stats[lbl]["fn"]
        total_tp += tp; total_fp += fp; total_fn += fn
        p  = tp / (tp + fp) if (tp + fp) else 0
        r  = tp / (tp + fn) if (tp + fn) else 0
        f1 = 2 * p * r / (p + r) if (p + r) else 0
        print(f"  {lbl:<12} {p:>10.3f} {r:>8.3f} {f1:>8.3f} {tp:>5} {fp:>5} {fn:>5}")

    # micro average
    micro_p  = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 0
    micro_r  = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 0
    micro_f1 = 2 * micro_p * micro_r / (micro_p + micro_r) if (micro_p + micro_r) else 0

    print(f"  {'-'*56}")
    print(f"  {'MICRO AVG':<12} {micro_p:>10.3f} {micro_r:>8.3f} {micro_f1:>8.3f}")
    print(f"\n  Micro F1 (realistic): {micro_f1:.4f}")
    print(f"  Target              : >= 0.70")
    print(f"  Status              : {'PASS' if micro_f1 >= 0.70 else 'NEEDS IMPROVEMENT'}")

    if errors:
        print(f"\n  First 10 errors:")
        for e in errors[:10]:
            print(e)


if __name__ == "__main__":
    main()
