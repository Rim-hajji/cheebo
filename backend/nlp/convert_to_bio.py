
import json
from pathlib import Path
from collections import Counter

def to_bio(text, entities):
    tokens = []
    positions = []
    pos = 0
    for tok in text.split():
        start = text.find(tok, pos)
        if start == -1:
            continue
        end = start + len(tok)
        tokens.append(tok)
        positions.append((start, end))
        pos = end

    labels = ['O'] * len(tokens)
    entities_sorted = sorted(entities, key=lambda x: x[0])

    for ent_start, ent_end, ent_label in entities_sorted:
        first = True
        for i, (tok_start, tok_end) in enumerate(positions):
            if tok_start >= ent_start and tok_end <= ent_end:
                labels[i] = 'B-' + ent_label if first else 'I-' + ent_label
                first = False
            elif tok_start < ent_end and tok_end > ent_start:
                labels[i] = 'B-' + ent_label if first else 'I-' + ent_label
                first = False

    return tokens, labels


base = Path('C:/Users/nesrin/Desktop/module_docto_agent/dataset_builder/data_real')
all_labels = Counter()
stats = {}

for split in ['train', 'val', 'test']:
    path = base / ('doctoagent_' + split + '_clean.json')
    if not path.exists():
        print('Fichier introuvable : ' + str(path))
        continue

    with open(path, encoding='utf-8') as f:
        data = json.load(f)

    bio_data = []
    for r in data:
        tokens, labels = to_bio(r['text'], r.get('entities', []))
        if len(tokens) == 0:
            continue
        bio_data.append({'tokens': tokens, 'ner_tags': labels})
        for lbl in labels:
            all_labels[lbl] += 1

    out = base / ('ner_bio_' + split + '.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(bio_data, f, ensure_ascii=False, indent=2)

    stats[split] = len(bio_data)
    print(split + ' : ' + str(len(bio_data)) + ' records -> ' + out.name)

label_list = sorted(all_labels.keys())
print('\nLabels BIO detectes :')
for lbl in label_list:
    print('  ' + lbl + ' : ' + str(all_labels[lbl]))

labels_path = base / 'ner_bio_labels.json'
with open(labels_path, 'w', encoding='utf-8') as f:
    json.dump(label_list, f, ensure_ascii=False, indent=2)
print('\nLabels sauves : ' + str(labels_path))

with open(base / 'ner_bio_train.json', encoding='utf-8') as f:
    sample = json.load(f)[0]
print('\n--- Exemple train[0] ---')
print('Tokens : ' + str(sample['tokens'][:10]))
print('Labels : ' + str(sample['ner_tags'][:10]))

print('\n=== RESUME ===')
print('Train  : ' + str(stats.get('train', 0)))
print('Val    : ' + str(stats.get('val', 0)))
print('Test   : ' + str(stats.get('test', 0)))
print('Labels : ' + str(len(label_list)))
