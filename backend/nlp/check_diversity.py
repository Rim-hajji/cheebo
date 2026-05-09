
import json
from pathlib import Path
from collections import Counter

data_path = Path("C:/Users/rim hajji/Desktop/module_docto_agent/dataset_builder/data_real/doctoagent_clean.json")
with open(data_path, encoding="utf-8") as f:
    data = json.load(f)

names = {0:"describe_symptom", 1:"ask_advice", 2:"emergency", 3:"follow_up"}

# Verifier la diversite des phrases ask_advice
ask_advice = [r for r in data if r["intent"] == 1]
print(f"Total ask_advice : {len(ask_advice)}")

# Sources
sources = Counter(r["source"] for r in ask_advice)
print(f"\nSources :")
for s,c in sources.most_common():
    print(f"  {s:<30} : {c}")

# Mots les plus frequents
from collections import Counter
import re
words = []
for r in ask_advice:
    words += re.findall(r'\b\w+\b', r["text"].lower())
word_freq = Counter(words)
print(f"\nTop 15 mots dans ask_advice :")
for w,c in word_freq.most_common(15):
    print(f"  {w:<20} : {c}")