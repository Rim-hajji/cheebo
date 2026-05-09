import spacy
import json
from pathlib import Path
from collections import Counter

print("Chargement modele hybride...")
nlp = spacy.load("models_v2/ner_model_hybrid")

# Charger le test set corrige
TEST_PATH = Path("C:/Users/rim hajji/Desktop/module_docto_agent/dataset_builder/data_real/doctoagent_test_clean.json")

with open(TEST_PATH, encoding="utf-8") as f:
    test_data = json.load(f)

print(f"Test set : {len(test_data)} records")

# Evaluation
tp = Counter()
fp = Counter()
fn = Counter()

for r in test_data:
    text     = r["text"]
    expected = {(e[0], e[1], e[2]) for e in r.get("entities", [])}

    doc       = nlp(text)
    predicted = {(e.start_char, e.end_char, e.label_) for e in doc.ents}

    for ent in predicted:
        if ent in expected:
            tp[ent[2]] += 1
        else:
            fp[ent[2]] += 1
    for ent in expected:
        if ent not in predicted:
            fn[ent[2]] += 1

# Calcul metriques
print("\n" + "=" * 55)
print("EVALUATION NER HYBRIDE — Test Set corrige (240 records)")
print("=" * 55)

print(f"\n{'Label':<12} {'Precision':>10} {'Recall':>10} {'F1':>10}")
print("-" * 44)

all_f1 = []
for label in ["ANIMAL", "SYMPTOM", "DUREE", "BODY_PART"]:
    p  = tp[label] / (tp[label] + fp[label]) if (tp[label] + fp[label]) > 0 else 0
    r  = tp[label] / (tp[label] + fn[label]) if (tp[label] + fn[label]) > 0 else 0
    f1 = 2 * p * r / (p + r) if (p + r) > 0 else 0
    all_f1.append(f1)
    print(f"  {label:<12} {p:>10.4f} {r:>10.4f} {f1:>10.4f}")

avg_f1 = sum(all_f1) / len(all_f1)
print(f"\n  {'MACRO AVG':<12} {'':>10} {'':>10} {avg_f1:>10.4f}")

# Global
total_tp  = sum(tp.values())
total_fp  = sum(fp.values())
total_fn  = sum(fn.values())
p_global  = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0
r_global  = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0
f1_global = 2 * p_global * r_global / (p_global + r_global) if (p_global + r_global) > 0 else 0

print(f"\n  Precision globale : {p_global:.4f}")
print(f"  Recall global     : {r_global:.4f}")
print(f"  F1 global         : {f1_global:.4f}")
print(f"\n  Entites attendues : {sum(tp.values()) + sum(fn.values())}")
print(f"  Entites predites  : {sum(tp.values()) + sum(fp.values())}")
print(f"  Vrais positifs    : {total_tp}")
print("=" * 55)

# 5 exemples
print("\n5 exemples de prediction :")
for r in test_data[:5]:
    doc      = nlp(r["text"])
    expected = [(e[0], e[1], e[2]) for e in r.get("entities", [])]
    print(f"\n  [{r['urgency']}] {r['text'][:80]}")
    print(f"  Attendu  : {[(r['text'][e[0]:e[1]], e[2]) for e in expected[:4]]}")
    print(f"  Detecte  : {[(e.text, e.label_) for e in doc.ents[:4]]}")