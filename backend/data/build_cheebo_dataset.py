#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_cheebo_dataset.py
========================
Combine toutes les parties et génère le fichier dataset final (2000 exemples).

Usage (Google Colab) :
    # 1. Uploader les 4 fichiers .py dans /content/
    # 2. Exécuter cette cellule :
    exec(open('build_cheebo_dataset.py').read())
    # Le dataset est dans la variable `final_dataset` et sauvegardé en JSON.

Usage local :
    python build_cheebo_dataset.py
"""

import json, random, sys, os
from pathlib import Path

random.seed(42)

# ─── Import des fichiers de scénarios ────────────────────────────────────────
HERE = Path(__file__).parent

def load_module(filename):
    """Charge un fichier .py et retourne son namespace."""
    path = HERE / filename
    ns = {}
    with open(path, encoding="utf-8") as f:
        exec(f.read(), ns)
    return ns

print("Chargement des scénarios…")
ns1 = load_module("generate_cheebo_dataset.py")
ns2 = load_module("cheebo_high_scenarios.py")
ns3 = load_module("cheebo_medium_low_scenarios.py")

CRITICAL = ns1["CRITICAL"]
HIGH     = ns2["HIGH"]
MEDIUM   = ns3["MEDIUM"]
LOW      = ns3["LOW"]

INSTRUCTION = ns1["INSTRUCTION"]

# ─── Générateur d'exemples ───────────────────────────────────────────────────

def build_input(level, animal, symptom, condition, care, red_flag):
    return (
        f"Niveau d'urgence : {level}\n"
        f"Animal : {animal}\n"
        f"Symptômes détectés : {symptom}\n"
        f"Conditions possibles : {condition}\n"
        f"Soins recommandés : {care}\n"
        f"Signes d'alarme : {red_flag}"
    )

def expand_scenario(scenario):
    """Produit (5 inputs) × (10 outputs) = 50 exemples par scénario."""
    level  = scenario["level"]
    animal = scenario["animal"]
    records = []
    for sym, cond, care, flag in zip(
        scenario["symptoms"], scenario["conditions"],
        scenario["cares"],    scenario["flags"]
    ):
        inp = build_input(level, animal, sym, cond, care, flag)
        for out in scenario["outputs"]:
            records.append({
                "instruction": INSTRUCTION,
                "input":       inp,
                "output":      out,
            })
    return records

# ─── Génération complète ──────────────────────────────────────────────────────

all_records = []
for grp_name, grp in [("CRITICAL", CRITICAL), ("HIGH", HIGH),
                       ("MEDIUM", MEDIUM),     ("LOW",  LOW)]:
    grp_records = []
    for sc in grp:
        grp_records.extend(expand_scenario(sc))
    print(f"  {grp_name:8s} : {len(sc['outputs'])} outputs × {len(sc['symptoms'])} inputs"
          f" × {len(grp)} scénarios = {len(grp_records)} exemples")
    all_records.extend(grp_records)

random.shuffle(all_records)

print(f"\nTotal généré : {len(all_records)} exemples")

# ─── Ajustement à exactement 2000 ────────────────────────────────────────────

TARGET = 2000
if len(all_records) < TARGET:
    # Dupliquer aléatoirement jusqu'à atteindre TARGET
    deficit = TARGET - len(all_records)
    extras  = random.choices(all_records, k=deficit)
    all_records.extend(extras)
    random.shuffle(all_records)
    print(f"  → Complétion à {TARGET} ({deficit} exemples dupliqués aléatoirement)")
else:
    all_records = all_records[:TARGET]
    print(f"  → Tronqué à {TARGET}")

print(f"Dataset final : {len(all_records)} exemples ✅")

# ─── Sauvegarde JSON ──────────────────────────────────────────────────────────

out_path = HERE / "cheebo_dataset_2000.json"
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(all_records, f, ensure_ascii=False, indent=2)

print(f"\nDataset sauvegardé → {out_path}")

# ─── Chargement Hugging Face Dataset ─────────────────────────────────────────

try:
    from datasets import Dataset

    dataset = Dataset.from_list(all_records)
    split   = dataset.train_test_split(test_size=0.1, seed=42)
    train_dataset = split["train"]
    test_dataset  = split["test"]

    print(f"\nEntraînement : {len(train_dataset)} exemples ✅")
    print(f"Test         : {len(test_dataset)} exemples ✅")

    # Exemple
    print("\n── Exemple aléatoire ──")
    ex = random.choice(all_records)
    print("INPUT  :", ex["input"][:200])
    print("OUTPUT :", ex["output"][:200])

    # Rendre disponible dans le namespace global (utile en Colab)
    import builtins
    builtins.train_dataset = train_dataset
    builtins.test_dataset  = test_dataset
    builtins.final_dataset = dataset

except ImportError:
    print("\n⚠️  'datasets' non installé — dataset disponible en JSON uniquement.")
    print(f"   Chemin : {out_path}")
