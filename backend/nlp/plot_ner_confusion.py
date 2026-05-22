"""
Matrice de confusion NER VetBERT v2 — niveau token (BIO tags).
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
import torch
from sklearn.metrics import confusion_matrix
from transformers import AutoTokenizer, AutoModelForTokenClassification

NLP_DIR    = Path(__file__).resolve().parent
MODELS_DIR = NLP_DIR / "models_v2"
BASE_DIR   = Path(__file__).resolve().parent.parent.parent
DATA_DIR   = BASE_DIR / "dataset_builder" / "data_real"
OUT_DIR    = NLP_DIR / "confusion_matrices"
OUT_DIR.mkdir(exist_ok=True)

TEST_NER_PATH = DATA_DIR / "ner_bio_test.json"


def plot_cm(cm, labels, title, filename, cmap="Oranges"):
    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.colorbar(im, ax=ax)

    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=9)
    ax.set_yticklabels(labels, fontsize=9)

    thresh = cm.max() / 2.0
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            val = cm[i, j]
            if val > 0:
                ax.text(j, i, str(val),
                        ha="center", va="center",
                        color="white" if val > thresh else "black",
                        fontsize=9, fontweight='bold')

    ax.set_xlabel("Prediction", fontsize=11)
    ax.set_ylabel("Vraie classe", fontsize=11)
    ax.set_title(title, fontsize=12, fontweight='bold', pad=12)
    plt.tight_layout()
    out_path = OUT_DIR / filename
    plt.savefig(out_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Sauvegarde -> {out_path}")


def main():
    ner_dir = MODELS_DIR / "ner_model_vetbert"
    print(f"Chargement NER <- {ner_dir.name} ...")

    tokenizer = AutoTokenizer.from_pretrained(str(ner_dir))
    model = AutoModelForTokenClassification.from_pretrained(
        str(ner_dir), torch_dtype=torch.float32
    )
    model.eval()
    id2label = model.config.id2label
    label2id = {v: k for k, v in id2label.items()}

    with open(TEST_NER_PATH, encoding="utf-8") as f:
        records = json.load(f)
    print(f"  {len(records)} sequences de test\n")

    all_true = []
    all_pred = []

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
        true_tags = true_tags[:len(tokens)]

        all_true.extend(true_tags)
        all_pred.extend(pred_tags)

    # Labels ordonnes : B- en premier, puis I-, puis O
    ordered_labels = [
        "B-ANIMAL", "I-ANIMAL",
        "B-SYMPTOM", "I-SYMPTOM",
        "B-BODY_PART", "I-BODY_PART",
        "B-DUREE", "I-DUREE",
        "O"
    ]

    cm = confusion_matrix(all_true, all_pred, labels=ordered_labels)

    # --- Matrice complete (tous les tags BIO) ---
    plot_cm(cm, ordered_labels,
            "Matrice de Confusion — NER VetBERT (tokens BIO)\n(ner_bio_test.json, 240 sequences)",
            "confusion_matrix_ner_bio.png", cmap="Oranges")

    # --- Matrice simplifiee (entites seulement, sans O) ---
    entity_labels = ["B-ANIMAL", "I-ANIMAL", "B-SYMPTOM", "I-SYMPTOM",
                     "B-BODY_PART", "I-BODY_PART", "B-DUREE", "I-DUREE"]
    entity_ids = [ordered_labels.index(l) for l in entity_labels]
    cm_ent = cm[np.ix_(entity_ids, list(range(len(ordered_labels))))]
    cm_ent_sq = cm[np.ix_(entity_ids, entity_ids)]

    plot_cm(cm_ent_sq, entity_labels,
            "Matrice de Confusion — NER VetBERT (entites uniquement)\n(confusion entre classes d'entites)",
            "confusion_matrix_ner_entities.png", cmap="Reds")

    # --- Stats token ---
    correct = sum(t == p for t, p in zip(all_true, all_pred))
    total   = len(all_true)
    print(f"  Tokens evalues : {total}")
    print(f"  Tokens corrects: {correct}  ({100*correct/total:.1f}%)")

    # Distribution des vraies classes
    from collections import Counter
    dist = Counter(all_true)
    print("\n  Distribution vraies classes :")
    for lbl in ordered_labels:
        print(f"    {lbl:<14} : {dist.get(lbl, 0):>5}")

    print("\nImages sauvegardees dans :", OUT_DIR)


if __name__ == "__main__":
    main()
