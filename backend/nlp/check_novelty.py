
import json
from pathlib import Path

# Phrases testées
test_phrases = [
    "My dog ate chocolate 30 minutes ago",
    "Mon chat a une bosse sur le ventre depuis une semaine",
    "My guinea pig stopped moving completely",
    "Should I brush my dog's teeth every day?",
    "My budgie fell from his perch and cannot fly tonight",
    "Yorkshire terrier has a swollen paw after playing",
    "My old tabby cat seems very weak and confused today",
    "URGENT my dog ate rat poison 2 hours ago",
    "My cat is having a seizure please help",
    "Is it safe to give my hamster fruit every day?",
]

# Charger le dataset complet
base = Path('C:/Users/nesrin/Desktop/module_docto_agent/dataset_builder/data_real')
all_texts = []

for split in ['train', 'val', 'test']:
    path = base / ('doctoagent_' + split + '_clean.json')
    if path.exists():
        with open(path, encoding='utf-8') as f:
            data = json.load(f)
        all_texts.extend([r['text'].lower().strip() for r in data])

print('Dataset total : ' + str(len(all_texts)) + ' records')
print('='*60)

for phrase in test_phrases:
    phrase_lower = phrase.lower().strip()

    # Recherche exacte
    exact = phrase_lower in all_texts

    # Recherche partielle (au moins 80% des mots en commun)
    words = set(phrase_lower.split())
    similar = []
    for text in all_texts:
        text_words = set(text.split())
        if len(words) > 0:
            overlap = len(words & text_words) / len(words)
            if overlap > 0.8 and text != phrase_lower:
                similar.append(text[:60])

    status = 'DANS DATASET' if exact else 'NOUVEAU'
    print('\n[' + status + '] ' + phrase[:60])
    if similar:
        print('  Similaire a : ' + similar[0])
    else:
        print('  Aucune phrase similaire trouvee')

