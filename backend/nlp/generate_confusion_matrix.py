
import numpy as np
import json
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
from sklearn.metrics import confusion_matrix, classification_report
import torch

print('Chargement des modeles...')

base = Path('models_v2')

# ── Intent ────────────────────────────────────────────────────────
print('\n' + '='*50)
print('MATRICE DE CONFUSION — INTENT')
print('='*50)

intent_pipe = pipeline('text-classification',
    model=str(base / 'intent_model'), top_k=1)

data_path = Path('../../dataset_builder/data_real/doctoagent_test_clean.json')
with open(data_path, encoding='utf-8') as f:
    test_data = json.load(f)

labels_map = {0:'describe_symptom', 1:'ask_advice', 2:'emergency', 3:'follow_up'}
label_names = ['describe_symptom', 'ask_advice', 'emergency', 'follow_up']

y_true_intent = []
y_pred_intent = []

for r in test_data:
    true_label = labels_map.get(r['intent'], 'describe_symptom')
    result = intent_pipe(r['text'][:512])[0]
    if isinstance(result, list):
        result = result[0]
    raw = result['label']
    label_map2 = {
        'LABEL_0':'describe_symptom','LABEL_1':'ask_advice',
        'LABEL_2':'emergency','LABEL_3':'follow_up',
        'describe_symptom':'describe_symptom','ask_advice':'ask_advice',
        'emergency':'emergency','follow_up':'follow_up',
    }
    pred_label = label_map2.get(raw, 'describe_symptom')
    y_true_intent.append(true_label)
    y_pred_intent.append(pred_label)

cm_intent = confusion_matrix(y_true_intent, y_pred_intent, labels=label_names)
print('\nMatrice de confusion Intent :')
print(f'{"":20}', end='')
for l in label_names:
    print(f'{l[:12]:>14}', end='')
print()
for i, row in enumerate(cm_intent):
    print(f'{label_names[i][:20]:20}', end='')
    for val in row:
        print(f'{val:>14}', end='')
    print()

print('\nRapport classification Intent :')
print(classification_report(y_true_intent, y_pred_intent, target_names=label_names))

# ── Urgency ───────────────────────────────────────────────────────
print('\n' + '='*50)
print('MATRICE DE CONFUSION — URGENCY')
print('='*50)

urgency_pipe = pipeline('text-classification',
    model=str(base / 'urgency_model'), top_k=1)

urgency_names = ['LOW', 'MODERATE', 'HIGH', 'CRITICAL']
urgency_map   = {'LABEL_0':'LOW','LABEL_1':'MODERATE','LABEL_2':'HIGH','LABEL_3':'CRITICAL',
                 'LOW':'LOW','MODERATE':'MODERATE','HIGH':'HIGH','CRITICAL':'CRITICAL'}

y_true_urg = []
y_pred_urg = []

for r in test_data:
    true_urg = r.get('urgency', 'LOW')
    result   = urgency_pipe(r['text'][:512])[0]
    if isinstance(result, list):
        result = result[0]
    pred_urg = urgency_map.get(result['label'], 'LOW')
    y_true_urg.append(true_urg)
    y_pred_urg.append(pred_urg)

cm_urg = confusion_matrix(y_true_urg, y_pred_urg, labels=urgency_names)
print('\nMatrice de confusion Urgency :')
print(f'{"":12}', end='')
for l in urgency_names:
    print(f'{l:>12}', end='')
print()
for i, row in enumerate(cm_urg):
    print(f'{urgency_names[i]:12}', end='')
    for val in row:
        print(f'{val:>12}', end='')
    print()

print('\nRapport classification Urgency :')
print(classification_report(y_true_urg, y_pred_urg, target_names=urgency_names))

print('\nSauvegarde...')
results = {
    'intent': {
        'confusion_matrix': cm_intent.tolist(),
        'labels': label_names,
    },
    'urgency': {
        'confusion_matrix': cm_urg.tolist(),
        'labels': urgency_names,
    }
}
with open('confusion_matrices.json', 'w') as f:
    json.dump(results, f, indent=2)
print('Sauvegarde : confusion_matrices.json')
