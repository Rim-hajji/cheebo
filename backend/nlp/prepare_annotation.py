
import json, random
from pathlib import Path

with open("../data/doctoagent_clean.json", encoding="utf-8") as f:
    data = json.load(f)

# Choisir 500 textes variés et difficiles
random.seed(42)

# Prioriser les textes avec animaux rares et symptomes variés
difficult = [r for r in data if len(r["text"].split()) > 8]
sample    = random.sample(difficult, min(500, len(difficult)))

# Format Label Studio
ls_data = [{"id": i, "text": r["text"]} for i, r in enumerate(sample)]

with open("to_annotate.json", "w", encoding="utf-8") as f:
    json.dump(ls_data, f, ensure_ascii=False, indent=2)

print(f"Fichier pret : {len(ls_data)} textes a annoter")
print("Importe to_annotate.json dans Label Studio")
