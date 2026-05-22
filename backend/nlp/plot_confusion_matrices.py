"""
Genere les matrices de confusion pour Intent et Urgency (VetBERT v2).
Sauvegarde dans backend/nlp/confusion_matrices/
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import confusion_matrix
from transformers import pipeline as hf_pipeline

BASE_DIR   = Path(__file__).resolve().parent.parent.parent
NLP_DIR    = Path(__file__).resolve().parent
MODELS_DIR = NLP_DIR / "models_v2"
DATA_DIR   = BASE_DIR / "dataset_builder" / "data_real"
OUT_DIR    = NLP_DIR / "confusion_matrices"
OUT_DIR.mkdir(exist_ok=True)

TEST_CLF_PATH = DATA_DIR / "doctoagent_test_clean.json"

INTENT_ID2LABEL  = {0: "describe_symptom", 1: "ask_advice", 2: "emergency", 3: "follow_up"}
URGENCY_ID2LABEL = {0: "LOW", 1: "MODERATE", 2: "HIGH", 3: "CRITICAL"}
URGENCY_LABEL2ID = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}


def get_predictions(clf, texts, id2label):
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
    return preds


def plot_cm(cm, labels, title, filename, cmap="Blues"):
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.colorbar(im, ax=ax)

    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=35, ha='right', fontsize=10)
    ax.set_yticklabels(labels, fontsize=10)

    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            ax.text(j, i, format(cm[i, j], 'd'),
                    ha="center", va="center",
                    color="white" if cm[i, j] > thresh else "black",
                    fontsize=12, fontweight='bold')

    ax.set_xlabel("Prediction", fontsize=11)
    ax.set_ylabel("Vraie classe", fontsize=11)
    ax.set_title(title, fontsize=13, fontweight='bold', pad=12)
    plt.tight_layout()
    out_path = OUT_DIR / filename
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Sauvegarde -> {out_path}")


def main():
    with open(TEST_CLF_PATH, encoding="utf-8") as f:
        data = json.load(f)

    texts       = [s["text"] for s in data]
    intent_ids  = [int(s["intent"]) for s in data]
    urgency_ids = [URGENCY_LABEL2ID[s["urgency"]] for s in data]

    # ── Intent ────────────────────────────────────────────────────
    print("Chargement Intent VetBERT ...")
    intent_clf = hf_pipeline(
        "text-classification",
        model=str(MODELS_DIR / "intent_model"),
        tokenizer=str(MODELS_DIR / "intent_model"),
        device=-1, truncation=True, max_length=128,
    )
    intent_preds = get_predictions(intent_clf, texts, INTENT_ID2LABEL)
    intent_labels = [INTENT_ID2LABEL[i] for i in sorted(INTENT_ID2LABEL)]
    cm_intent = confusion_matrix(intent_ids, intent_preds)
    plot_cm(cm_intent, intent_labels,
            "Matrice de Confusion — Intent VetBERT\n(test reel, 180 samples)",
            "confusion_matrix_intent.png", cmap="Blues")

    # ── Urgency ───────────────────────────────────────────────────
    print("Chargement Urgency VetBERT ...")
    urgency_clf = hf_pipeline(
        "text-classification",
        model=str(MODELS_DIR / "urgency_model"),
        tokenizer=str(MODELS_DIR / "urgency_model"),
        device=-1, truncation=True, max_length=128,
    )
    urgency_preds = get_predictions(urgency_clf, texts, URGENCY_ID2LABEL)
    urgency_labels = [URGENCY_ID2LABEL[i] for i in sorted(URGENCY_ID2LABEL)]
    cm_urgency = confusion_matrix(urgency_ids, urgency_preds)
    plot_cm(cm_urgency, urgency_labels,
            "Matrice de Confusion — Urgency VetBERT\n(test reel, 180 samples)",
            "confusion_matrix_urgency.png", cmap="Greens")

    print("\nImages sauvegardees dans :", OUT_DIR)


if __name__ == "__main__":
    main()
