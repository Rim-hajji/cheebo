"""
fix_imbalance_vetbert.py
========================
Corrige le déséquilibre de classes INTENT pour VetBERT.

Problème détecté :
  describe_symptom : 169 (test) → ~1300 (train)
  emergency        :  41 (test) → ~315 (train)
  follow_up        :  18 (test) → ~138 (train)
  ask_advice       :  16 (test) → ~122 (train)

Stratégies combinées :
  1. Oversampling (SMOTE-like) — dupliquer les exemples rares avec variation
  2. Augmentation textuelle — synonymes + reformulation + templates
  3. Weighted Loss corrigé — poids inversement proportionnels à la fréquence
  4. Under-sampling de describe_symptom si nécessaire

TARGET : ~500 exemples par classe dans le train set

Usage :
  cd backend/nlp
  python fix_imbalance_vetbert.py --check      # voir la distribution actuelle
  python fix_imbalance_vetbert.py --fix        # créer dataset équilibré
  python fix_imbalance_vetbert.py --train      # entraîner VetBERT sur données équilibrées
"""

import argparse
import json
import random
import re
from collections import Counter
from pathlib import Path

import numpy as np

random.seed(42)
np.random.seed(42)

# ─── CHEMINS ────────────────────────────────────────────────────────────────
DATA_PATH   = Path("../../dataset_builder/data_real/doctoagent_clean.json")
OUTPUT_PATH = Path("../../dataset_builder/data_real/doctoagent_balanced.json")

INTENT_NAMES = {0: "describe_symptom", 1: "ask_advice", 2: "emergency", 3: "follow_up"}
TARGET_PER_CLASS = 500   # objectif par classe

# ─── TEMPLATES DE REFORMULATION PAR CLASSE ──────────────────────────────────

# ask_advice (classe 1) — questions de conseil général
ASK_ADVICE_TEMPLATES = [
    "My {animal} has been {symptom}, should I be worried?",
    "Is it normal for {animal} to {symptom}?",
    "Do I need to see a vet if my {animal} {symptom}?",
    "My {animal} {symptom}, what should I do?",
    "Can I treat my {animal}'s {symptom} at home?",
    "How serious is it if a {animal} {symptom}?",
    "Should I be concerned about my {animal} {symptom}?",
    "My {animal} seems {symptom}, is that a problem?",
    "When should I take my {animal} to the vet for {symptom}?",
    "Is {symptom} in {animal}s dangerous?",
    "What can I give my {animal} for {symptom}?",
    "Is it safe to wait and see if my {animal}'s {symptom} gets better?",
    "My {animal} started {symptom} yesterday, should I call the vet?",
    "How do I know if my {animal}'s {symptom} is serious?",
    "My vet is closed and my {animal} is {symptom}, what can I do?",
    # Français
    "Mon {animal_fr} {symptom_fr}, est-ce que je dois aller chez le vétérinaire ?",
    "Est-ce normal que mon {animal_fr} {symptom_fr} ?",
    "Mon {animal_fr} semble {symptom_fr}, dois-je m'inquiéter ?",
    "Que faire si mon {animal_fr} {symptom_fr} ?",
    "Mon {animal_fr} {symptom_fr} depuis hier, c'est grave ?",
]

# follow_up (classe 3) — suivi après traitement
FOLLOW_UP_TEMPLATES = [
    "My {animal} finished the antibiotics 3 days ago and still {symptom}.",
    "After the surgery, my {animal} is {symptom}. Is that normal?",
    "My {animal} had treatment last week but is still {symptom}.",
    "Following up on my {animal}'s {symptom} — no improvement after 5 days.",
    "My {animal} was diagnosed with {condition} last month, now {symptom}.",
    "We completed the treatment but my {animal} {symptom} again.",
    "My {animal} was doing better but now {symptom} returned.",
    "The vet prescribed {medication} but my {animal} is still {symptom}.",
    "Post-op check: my {animal} is {symptom} at day 4 after surgery.",
    "My {animal} had blood work done, now {symptom} appeared.",
    "Update on my {animal}: the {symptom} is not getting better.",
    "My {animal} recovered from the infection but now has {symptom}.",
    # Français
    "Mon {animal_fr} a terminé les antibiotiques mais {symptom_fr} encore.",
    "Après l'opération, mon {animal_fr} {symptom_fr}. C'est normal ?",
    "Suivi : mon {animal_fr} {symptom_fr} toujours après le traitement.",
    "Mon {animal_fr} avait guéri mais {symptom_fr} est réapparu.",
]

# emergency (classe 2) — urgences
EMERGENCY_TEMPLATES = [
    "URGENT: my {animal} is {symptom} and can't breathe properly!",
    "My {animal} just collapsed and is {symptom}, I need help now!",
    "Emergency: {animal} is {symptom} and unresponsive.",
    "My {animal} swallowed {object} and is {symptom}, call vet?",
    "My {animal} is {symptom} and has been for 2 hours, very worried.",
    "Help! My {animal} is {symptom} and I don't know what to do.",
    "My {animal} was hit by a car and is {symptom}.",
    "URGENT: my {animal} ate {object} and is {symptom}.",
    "My {animal} is {symptom} and trembling, is this serious?",
    "Emergency: my {animal} is {symptom} and the vet is closed.",
    # Français
    "URGENT : mon {animal_fr} {symptom_fr} et ne respire plus normalement !",
    "Mon {animal_fr} vient de s'effondrer et {symptom_fr}, aidez-moi !",
    "Urgence : mon {animal_fr} {symptom_fr} depuis 1 heure.",
    "Mon {animal_fr} a avalé {object_fr} et {symptom_fr}, que faire ?",
]

# ─── VOCABULAIRE ─────────────────────────────────────────────────────────────
ANIMALS_EN = ["dog", "cat", "rabbit", "hamster", "parrot", "ferret", "bird", "turtle", "guinea pig", "rat"]
ANIMALS_FR = ["chien", "chat", "lapin", "hamster", "perroquet", "furet", "oiseau", "tortue", "cochon d'inde", "rat"]

SYMPTOMS_EN = [
    "limping", "vomiting", "not eating", "lethargic", "scratching",
    "sneezing", "coughing", "drinking a lot", "losing weight", "has diarrhea",
    "shaking", "whimpering", "has a discharge", "is pale", "is not responsive",
    "bleeding", "has difficulty walking", "is in pain", "has swollen legs",
]
SYMPTOMS_FR = [
    "boite", "vomit", "ne mange plus", "est abattu", "se gratte",
    "éternue", "tousse", "boit beaucoup", "maigrit", "a la diarrhée",
    "tremble", "gémit", "a des écoulements", "est pâle", "ne répond plus",
    "saigne", "a du mal à marcher", "souffre", "a les pattes gonflées",
]

CONDITIONS = ["infection", "kidney disease", "diabetes", "arthritis", "pancreatitis"]
MEDICATIONS = ["antibiotics", "steroids", "pain medication", "the treatment", "the medication"]
OBJECTS_EN = ["a grape", "chocolate", "a toy", "rat poison", "a bone", "a coin"]
OBJECTS_FR = ["un raisin", "du chocolat", "un jouet", "de la mort-aux-rats", "un os", "une pièce"]


def fill_template(template: str) -> str:
    """Remplit un template avec du vocabulaire aléatoire."""
    a_en = random.choice(ANIMALS_EN)
    a_fr = random.choice(ANIMALS_FR)
    s_en = random.choice(SYMPTOMS_EN)
    s_fr = random.choice(SYMPTOMS_FR)

    return (template
        .replace("{animal}", a_en)
        .replace("{animal_fr}", a_fr)
        .replace("{symptom}", s_en)
        .replace("{symptom_fr}", s_fr)
        .replace("{condition}", random.choice(CONDITIONS))
        .replace("{medication}", random.choice(MEDICATIONS))
        .replace("{object}", random.choice(OBJECTS_EN))
        .replace("{object_fr}", random.choice(OBJECTS_FR))
    )


def generate_from_templates(templates: list, intent_id: int, n: int) -> list:
    """Génère n exemples depuis les templates."""
    samples = []
    seen = set()
    attempts = 0
    while len(samples) < n and attempts < n * 10:
        attempts += 1
        tmpl = random.choice(templates)
        text = fill_template(tmpl)
        if text not in seen:
            seen.add(text)
            samples.append({
                "text": text,
                "intent": intent_id,
                "urgency": "LOW" if intent_id in (1, 3) else "HIGH",
                "entities": [],
                "source": "template_generation",
                "language": "en" if not any(c in text for c in "àéèêëîïôùûüç") else "fr",
            })
    return samples


# ─── AUGMENTATION TEXTUELLE ──────────────────────────────────────────────────

SYNONYMS = {
    "dog": ["canine", "puppy", "pup", "pooch"],
    "cat": ["feline", "kitten", "kitty"],
    "vet": ["veterinarian", "animal doctor", "vet clinic"],
    "sick": ["unwell", "ill", "not well"],
    "normal": ["usual", "common", "expected"],
    "worried": ["concerned", "anxious", "scared"],
    "symptoms": ["signs", "issues", "problems"],
    "treatment": ["therapy", "medication", "medicine"],
    "eating": ["feeding", "food intake", "appetite"],
}

def text_augment(text: str) -> str:
    """Augmentation légère par substitution de synonymes."""
    words = text.split()
    for i, word in enumerate(words):
        clean = word.lower().strip(".,!?;:")
        if clean in SYNONYMS and random.random() < 0.3:
            replacement = random.choice(SYNONYMS[clean])
            words[i] = word.replace(clean, replacement)
    return " ".join(words)


def oversample_with_augmentation(samples: list, target: int) -> list:
    """Oversample une classe en augmentant les textes existants."""
    result = list(samples)
    seen = {s["text"] for s in result}

    attempts = 0
    while len(result) < target and attempts < (target - len(samples)) * 20:
        attempts += 1
        orig = random.choice(samples)
        new_text = text_augment(orig["text"])
        if new_text not in seen and new_text != orig["text"]:
            seen.add(new_text)
            new_item = dict(orig)
            new_item["text"] = new_text
            new_item["source"] = orig.get("source", "real") + "_aug"
            result.append(new_item)

    return result


# ─── DIAGNOSTIC ──────────────────────────────────────────────────────────────

def show_distribution(data: list, title: str = "Distribution"):
    print(f"\n{'─'*50}")
    print(f"  {title}")
    print(f"{'─'*50}")
    intent_counts = Counter(d.get("intent") for d in data if d.get("intent") is not None)
    total = sum(intent_counts.values())
    for intent_id, name in INTENT_NAMES.items():
        count = intent_counts.get(intent_id, 0)
        bar = "█" * (count * 30 // max(intent_counts.values(), default=1))
        pct = count / total * 100 if total else 0
        status = "✅" if count >= TARGET_PER_CLASS else ("⚠️" if count >= 100 else "❌")
        print(f"  {status} {name:<22} : {count:>5} ({pct:.1f}%) {bar}")
    print(f"  {'TOTAL':<22} : {total:>5}")

    # Ratio déséquilibre
    if intent_counts:
        max_c = max(intent_counts.values())
        min_c = min(intent_counts.values())
        ratio = max_c / min_c if min_c > 0 else float("inf")
        status = "✅ OK" if ratio < 3 else ("⚠️ Modéré" if ratio < 10 else "❌ Sévère")
        print(f"\n  Ratio déséquilibre : {ratio:.1f}x  →  {status}")


def compute_class_weights_display(data: list) -> dict:
    """Calcule les poids de classes recommandés pour WeightedTrainer."""
    counts = Counter(d.get("intent") for d in data if d.get("intent") is not None)
    total = sum(counts.values())
    n_classes = len(counts)
    weights = {}
    for intent_id in INTENT_NAMES:
        count = counts.get(intent_id, 1)
        weights[intent_id] = min(total / (n_classes * count), 10.0)
    return weights


# ─── ÉQUILIBRAGE ─────────────────────────────────────────────────────────────

def balance_dataset(data: list) -> list:
    """
    Équilibre le dataset :
    1. Regroupe par classe
    2. Génère depuis templates pour les classes très minoritaires
    3. Oversampling avec augmentation textuelle
    4. Undersampling de describe_symptom si nécessaire
    """
    by_class = {i: [] for i in INTENT_NAMES}
    for d in data:
        intent = d.get("intent")
        if intent in by_class:
            by_class[intent].append(d)

    # Mapping templates par classe
    templates_map = {
        1: ASK_ADVICE_TEMPLATES,     # ask_advice
        2: EMERGENCY_TEMPLATES,      # emergency
        3: FOLLOW_UP_TEMPLATES,      # follow_up
    }

    balanced = []
    for intent_id, name in INTENT_NAMES.items():
        samples = by_class[intent_id]
        current = len(samples)
        print(f"\n  [{name}] : {current} → cible {TARGET_PER_CLASS}")

        if intent_id == 0:
            # describe_symptom : undersample si trop grand
            if current > TARGET_PER_CLASS:
                random.shuffle(samples)
                samples = samples[:TARGET_PER_CLASS]
                print(f"    ↓ Under-sampled → {len(samples)}")
            balanced.extend(samples)

        else:
            # Classes minoritaires : générer d'abord depuis templates
            if current < 50 and intent_id in templates_map:
                n_generate = min(TARGET_PER_CLASS // 2, 300)
                generated = generate_from_templates(templates_map[intent_id], intent_id, n_generate)
                samples = samples + generated
                print(f"    + Template generation → +{len(generated)} = {len(samples)}")

            # Puis oversampling avec augmentation
            if len(samples) < TARGET_PER_CLASS:
                samples = oversample_with_augmentation(samples, TARGET_PER_CLASS)
                print(f"    + Oversampling (augmentation) → {len(samples)}")

            balanced.extend(samples)

    random.shuffle(balanced)
    return balanced


# ─── CALCUL POIDS POUR TRAINING ─────────────────────────────────────────────

def print_recommended_weights(data: list):
    weights = compute_class_weights_display(data)
    print(f"\n{'─'*50}")
    print("  Poids recommandés pour WeightedTrainer :")
    print(f"{'─'*50}")
    for intent_id, name in INTENT_NAMES.items():
        w = weights.get(intent_id, 1.0)
        print(f"  {name:<22} : {w:.3f}")
    print(f"\n  Code à mettre dans train_all_models_v2.py :")
    weights_list = [round(weights.get(i, 1.0), 3) for i in range(4)]
    print(f"  class_weights = torch.tensor({weights_list}, dtype=torch.float)")


# ─── ENTRY POINT ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Correction déséquilibre classes VetBERT")
    parser.add_argument("--check", action="store_true", help="Afficher la distribution actuelle")
    parser.add_argument("--fix",   action="store_true", help="Créer le dataset équilibré")
    parser.add_argument("--train", action="store_true", help="Lancer l'entraînement VetBERT après correction")
    args = parser.parse_args()

    if not any([args.check, args.fix, args.train]):
        parser.print_help()
        return

    # Charger dataset
    data_path = DATA_PATH
    if not data_path.exists():
        # Essayer chemin depuis nlp/
        alt = Path("C:/Users/nesrin/Desktop/module_docto_agent/dataset_builder/data_real/doctoagent_clean.json")
        if alt.exists():
            data_path = alt
        else:
            print(f"[ERREUR] Dataset introuvable : {DATA_PATH}")
            return

    print(f"\nChargement : {data_path}")
    data = json.loads(data_path.read_text(encoding="utf-8"))
    print(f"Total : {len(data)} enregistrements")

    # ── CHECK ──────────────────────────────────────────────────────────────
    if args.check or args.fix:
        show_distribution(data, "Distribution AVANT équilibrage")
        print_recommended_weights(data)

    if args.fix:
        # Séparer les données avec intent de celles sans
        with_intent    = [d for d in data if d.get("intent") is not None]
        without_intent = [d for d in data if d.get("intent") is None]

        print(f"\n{len(with_intent)} enregistrements avec intent label")
        print(f"Équilibrage en cours...")

        balanced = balance_dataset(with_intent)
        show_distribution(balanced, "Distribution APRÈS équilibrage")
        print_recommended_weights(balanced)

        # Réintégrer les enregistrements sans intent
        final = balanced + without_intent

        out_path = OUTPUT_PATH
        if not out_path.parent.exists():
            out_path = Path("C:/Users/nesrin/Desktop/module_docto_agent/dataset_builder/data_real/doctoagent_balanced.json")

        out_path.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n✅ Dataset équilibré sauvegardé : {out_path}")
        print(f"   ({len(balanced)} exemples avec intent, {len(without_intent)} sans)")
        print(f"\n   Prochaine étape :")
        print(f"   python train_all_models_v2.py --fast --task intent")
        print(f"   (après avoir modifié DATASET_PATH dans train_all_models_v2.py)")

    if args.train:
        print("\n[INFO] Lance l'entraînement VetBERT sur le dataset équilibré...")
        import subprocess, sys
        subprocess.run([
            sys.executable, "train_all_models_v2.py",
            "--fast", "--task", "intent"
        ])


if __name__ == "__main__":
    main()
