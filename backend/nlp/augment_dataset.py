"""
Standalone augmentation script (data preparation only).

WARNING — do NOT use these output files as direct training inputs.
train_all_models.py augments the TRAINING SPLIT ONLY after splitting.
Running this script is only useful to inspect augmented data or to
pre-build the NER augmented dataset (ner_dataset_aug.jsonl).

For classification (intent/urgency): use train_all_models.py --use-aug
which handles augmentation correctly (split first, then augment train).

Techniques:
  1. Veterinary synonym substitution (FR vocabulary, manual + NLTK WordNet FR)
  2. Sentence template paraphrase
  3. Prefix / suffix injection
  4. Minority-class oversampling
"""

import hashlib
import json
import os
import random
from collections import Counter

import nltk
from nltk.corpus import wordnet as wn

# Download required NLTK corpora once
for _corpus in ("wordnet", "omw-1.4"):
    try:
        nltk.data.find(f"corpora/{_corpus}")
    except LookupError:
        nltk.download(_corpus, quiet=True)


def get_wordnet_synonyms(word: str, lang: str = "fra", max_syns: int = 5) -> list[str]:
    """Return up to max_syns French synonyms for word via NLTK Open Multilingual Wordnet."""
    synonyms: list[str] = []
    for synset in wn.synsets(word, lang=lang):
        for lemma in synset.lemma_names(lang=lang):
            clean = lemma.replace("_", " ").lower()
            if clean != word.lower() and clean not in synonyms:
                synonyms.append(clean)
        if len(synonyms) >= max_syns:
            break
    return synonyms[:max_syns]

SEED = 42
random.seed(SEED)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR  = os.path.join(BASE_DIR, "data")

INTENT_IN   = os.path.join(DATA_DIR, "intent_dataset.json")
URGENCY_IN  = os.path.join(DATA_DIR, "urgency_dataset.jsonl")
INTENT_OUT  = os.path.join(DATA_DIR, "intent_dataset_aug.json")
URGENCY_OUT = os.path.join(DATA_DIR, "urgency_dataset_aug.jsonl")

TARGET_PER_CLASS_INTENT  = 1000   # aim for ~1000 samples per intent class
TARGET_PER_CLASS_URGENCY = 900    # aim for ~900 per urgency class

# ── veterinary synonym table (FR) ─────────────────────────────────────────────
SYNONYMS: dict[str, list[str]] = {
    # animals
    "chien":          ["chien", "toutou", "canidé", "animal"],
    "chat":           ["chat", "félin", "minou", "animal"],
    "lapin":          ["lapin", "lapereau", "animal"],
    "hamster":        ["hamster", "animal"],
    "perroquet":      ["perroquet", "psittacidé", "oiseau", "animal"],
    "furet":          ["furet", "mustélidé", "animal"],
    "oiseau":         ["oiseau", "volatile", "animal"],
    "tortue":         ["tortue", "reptile", "animal"],
    "cheval":         ["cheval", "équidé", "animal"],
    "cochon d'inde":  ["cochon d'inde", "cobaye", "animal"],
    "rat":            ["rat", "rongeur", "animal"],
    "reptile":        ["reptile", "lézard", "animal"],

    # symptoms
    "vomit":          ["vomit", "régurgite", "rend"],
    "diarrhée":       ["diarrhée", "selles molles", "colite"],
    "tousse":         ["tousse", "est enrhumé", "a une toux"],
    "éternue":        ["éternue", "a des éternuements", "renifle"],
    "boite":          ["boite", "claudique", "marche mal"],
    "saigne":         ["saigne", "perd du sang", "hémorragie"],
    "convulse":       ["convulse", "a des convulsions", "tremble"],
    "inconscient":    ["inconscient", "sans connaissance", "ne répond pas"],
    "paralysé":       ["paralysé", "ne peut plus bouger", "immobile"],
    "fatigue":        ["fatigué", "abattu", "prostré", "léthargique"],
    "mange":          ["mange", "s'alimente", "prend sa nourriture"],
    "boit":           ["boit", "s'hydrate", "consomme de l'eau"],
    "gratte":         ["se gratte", "se démange", "se frotte"],
    "perd ses poils": ["perd ses poils", "a de l'alopécie", "perd sa fourrure"],

    # modifiers
    "beaucoup":       ["beaucoup", "énormément", "fréquemment"],
    "peu":            ["peu", "rarement", "légèrement"],
    "depuis":         ["depuis", "cela fait"],
    "grave":          ["grave", "sérieux", "sévère"],
    "normal":         ["normal", "habituel", "courant"],
}


def apply_synonyms(text: str, n_swaps: int = 1) -> str:
    """Replace n_swaps words/phrases using manual table first, then NLTK WordNet FR."""
    result = text
    lower  = result.lower()
    swapped = 0

    # 1. Manual veterinary table (priority — domain-specific)
    keys = list(SYNONYMS.keys())
    random.shuffle(keys)
    for key in keys:
        if swapped >= n_swaps:
            break
        if key in lower:
            replacement = random.choice(SYNONYMS[key])
            idx = lower.find(key)
            if idx >= 0:
                result = result[:idx] + replacement + result[idx + len(key):]
                lower  = result.lower()
                swapped += 1

    # 2. NLTK WordNet FR fallback — for words not covered by manual table
    if swapped < n_swaps:
        words = result.split()
        random.shuffle(words)
        for word in words:
            if swapped >= n_swaps:
                break
            clean = word.lower().strip(".,!?;:")
            if clean in SYNONYMS:
                continue  # already handled above
            wn_syns = get_wordnet_synonyms(clean, lang="fra")
            if wn_syns:
                replacement = random.choice(wn_syns)
                idx = result.lower().find(clean)
                if idx >= 0:
                    result = result[:idx] + replacement + result[idx + len(clean):]
                    swapped += 1

    return result


# ── prefix / suffix pools ─────────────────────────────────────────────────────
PREFIXES = [
    "", "", "",                    # keep original phrasing most of the time
    "Bonjour, ",
    "Bonsoir, ",
    "Salut, ",
    "Bonjour à tous, ",
    "Aidez-moi svp, ",
    "Question urgente : ",
    "Bonsoir docteur, ",
    "S'il vous plaît, ",
]

QUESTION_SUFFIXES = [
    "",
    " Que faire ?",
    " Est-ce normal ?",
    " Dois-je aller chez le vétérinaire ?",
    " Avez-vous des conseils ?",
    " C'est grave ?",
    " Que conseillez-vous ?",
]


def add_framing(text: str) -> str:
    """Add a realistic prefix and/or question suffix."""
    prefix = random.choice(PREFIXES)
    suffix = random.choice(QUESTION_SUFFIXES)
    result = text.strip()
    if prefix and not result.startswith(tuple(p.strip(", ") for p in PREFIXES if p)):
        result = prefix + result[0].lower() + result[1:]
    if suffix and not result.endswith("?"):
        result = result.rstrip(".!") + suffix
    return result


# ── paraphrase templates (same semantics, different structure) ─────────────────
PARAPHRASE_RULES: list[tuple[str, str]] = [
    # (pattern substring, replacement template using {rest})
    ("mon {a} ne mange plus",
     "depuis quelque temps, mon {a} refuse toute nourriture"),
    ("mon {a} vomit",
     "mon {a} a des vomissements"),
    ("mon {a} a la diarrhée",
     "mon {a} souffre de diarrhée"),
    ("mon {a} se gratte",
     "mon {a} présente des démangeaisons"),
    ("mon {a} tousse",
     "mon {a} a une toux persistante"),
    ("mon {a} boite",
     "mon {a} présente une boiterie"),
    ("mon {a} perd ses poils",
     "mon {a} a de l'alopécie"),
    ("mon {a} est inconscient",
     "mon {a} ne répond plus et semble inconscient"),
    ("mon {a} convulse",
     "mon {a} a des crises convulsives"),
    ("mon {a} saigne",
     "mon {a} présente un saignement"),
]

ANIMALS = [
    "chien", "chat", "lapin", "hamster", "perroquet", "furet",
    "oiseau", "tortue", "cheval", "cochon d'inde", "rat", "reptile",
]


def paraphrase(text: str) -> str | None:
    """Try to apply a paraphrase rule; return None if none match."""
    t = text.lower()
    for pattern, tmpl in PARAPHRASE_RULES:
        # find which animal is in the text
        for a in ANIMALS:
            filled_pattern = pattern.replace("{a}", a)
            if filled_pattern in t:
                new_text = tmpl.replace("{a}", a)
                # preserve original capitalisation style
                return new_text[0].upper() + new_text[1:]
    return None


# ── core augmentation ──────────────────────────────────────────────────────────

def _norm(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _hash(text: str) -> str:
    return hashlib.md5(_norm(text).encode()).hexdigest()


def augment_samples(
    samples: list[dict],
    target_total: int,
    label_key: str,
) -> list[dict]:
    """
    Augment a list of samples to reach target_total via:
      - synonym substitution (manual dict + NLTK WordNet FR)
      - framing variation
      - paraphrase
    Maintains class balance: oversamples minority classes first.
    """
    seen: set[str] = {_hash(s["text"]) for s in samples}
    result = list(samples)

    label_counts = Counter(s[label_key] for s in samples)
    max_label_count = max(label_counts.values())

    # How many new samples do we need?
    needed = max(0, target_total - len(result))
    if needed == 0:
        return result

    # Build a weighted pool: minority classes get higher weight
    weights = {lbl: max_label_count / cnt for lbl, cnt in label_counts.items()}
    pool = [(s, weights[s[label_key]]) for s in samples]

    attempts = 0
    while len(result) < target_total and attempts < needed * 20:
        attempts += 1
        # weighted random pick
        items, wts = zip(*pool)
        (orig,) = random.choices(items, weights=wts, k=1)
        text = orig["text"]

        # choose augmentation strategy
        strategy = random.choice(["synonym", "framing", "paraphrase", "combined"])

        if strategy == "synonym":
            new_text = apply_synonyms(text, n_swaps=random.randint(1, 2))
        elif strategy == "framing":
            new_text = add_framing(text)
        elif strategy == "paraphrase":
            p = paraphrase(text)
            new_text = p if p else add_framing(text)
        else:  # combined
            new_text = apply_synonyms(add_framing(text), n_swaps=1)

        if new_text == text:
            continue

        h = _hash(new_text)
        if h in seen:
            continue

        seen.add(h)
        new_item = dict(orig)
        new_item["text"] = new_text
        result.append(new_item)

    random.shuffle(result)
    return result


# ── intent dataset ─────────────────────────────────────────────────────────────

def process_intent():
    print("\n=== INTENT AUGMENTATION ===")
    with open(INTENT_IN, "r", encoding="utf-8") as f:
        data = json.load(f)

    label_counts = Counter(s["label"] for s in data)
    print(f"  Before: {len(data)} samples | distribution: {dict(label_counts)}")

    # how many total we want
    n_classes = len(label_counts)
    target_total = TARGET_PER_CLASS_INTENT * n_classes

    augmented = augment_samples(data, target_total, label_key="label")

    label_counts_after = Counter(s["label"] for s in augmented)
    print(f"  After:  {len(augmented)} samples | distribution: {dict(label_counts_after)}")

    with open(INTENT_OUT, "w", encoding="utf-8") as f:
        json.dump(augmented, f, ensure_ascii=False, indent=2)
    print(f"  Saved -> {INTENT_OUT}")

    # also merge synthetic_extra if available
    synth_path = os.path.join(DATA_DIR, "synthetic_extra.jsonl")
    if os.path.exists(synth_path):
        print("  Merging synthetic_extra.jsonl …")
        seen_hashes = {_hash(s["text"]) for s in augmented}
        extras = []
        with open(synth_path, "r", encoding="utf-8") as f:
            for line in f:
                item = json.loads(line)
                h = _hash(item["text"])
                if h not in seen_hashes and "label" in item:
                    seen_hashes.add(h)
                    extras.append({"text": item["text"], "label": item["label"]})
        augmented.extend(extras)
        random.shuffle(augmented)
        print(f"  After merge: {len(augmented)} samples")
        with open(INTENT_OUT, "w", encoding="utf-8") as f:
            json.dump(augmented, f, ensure_ascii=False, indent=2)

    return augmented


# ── urgency dataset ────────────────────────────────────────────────────────────

def process_urgency():
    print("\n=== URGENCY AUGMENTATION ===")
    data = []
    with open(URGENCY_IN, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))

    label_counts = Counter(s["label"] for s in data)
    print(f"  Before: {len(data)} samples | distribution: {dict(label_counts)}")

    n_classes = len(label_counts)
    target_total = TARGET_PER_CLASS_URGENCY * n_classes

    augmented = augment_samples(data, target_total, label_key="label")

    label_counts_after = Counter(s["label"] for s in augmented)
    print(f"  After:  {len(augmented)} samples | distribution: {dict(label_counts_after)}")

    with open(URGENCY_OUT, "w", encoding="utf-8") as f:
        for item in augmented:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"  Saved -> {URGENCY_OUT}")

    # merge scraped data if available
    scraped_path = os.path.join(DATA_DIR, "scraped_wamiz.jsonl")
    if os.path.exists(scraped_path):
        print("  Merging scraped_wamiz.jsonl …")
        seen_hashes = {_hash(s["text"]) for s in augmented}
        extras = []
        with open(scraped_path, "r", encoding="utf-8") as f:
            for line in f:
                item = json.loads(line)
                h = _hash(item["text"])
                if h not in seen_hashes and "urgency" in item:
                    seen_hashes.add(h)
                    extras.append({"text": item["text"], "label": item["urgency"]})
        augmented.extend(extras)
        random.shuffle(augmented)
        print(f"  After scrape merge: {len(augmented)} samples")
        with open(URGENCY_OUT, "w", encoding="utf-8") as f:
            for item in augmented:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")

    return augmented


# ── entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not os.path.exists(INTENT_IN):
        print(f"[error] Not found: {INTENT_IN}")
    else:
        process_intent()

    if not os.path.exists(URGENCY_IN):
        print(f"[error] Not found: {URGENCY_IN}")
    else:
        process_urgency()

    print("\n=== AUGMENTATION COMPLETE ===")
    print("Next step: python backend/nlp/train_all_models.py")
