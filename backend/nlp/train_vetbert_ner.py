"""
DoctoAgent - VetBERT NER
========================
Token Classification : ANIMAL, SYMPTOM, BODY_PART, DUREE

Fichiers attendus dans BASE :
  - ner_bio_labels.json
  - ner_bio_train.json
  - ner_bio_val.json
  - ner_bio_test.json

Usage :
  py train_ner_vetbert.py
"""

import json
import numpy as np
from pathlib import Path
from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    TrainingArguments,
    Trainer,
    DataCollatorForTokenClassification,
)
from torch.utils.data import Dataset
import torch
from seqeval.metrics import f1_score, precision_score, recall_score, classification_report

print('=' * 60)
print('VETBERT NER — Token Classification')
print('=' * 60)

# ──────────────────────────────────────────────────────────────────
# CONFIGURATION — modifier uniquement BASE si besoin
# ──────────────────────────────────────────────────────────────────
BASE       = Path(__file__).resolve().parent.parent.parent / "dataset_builder" / "data_real"
MODEL_NAME = 'havocy28/VetBERT'
OUTPUT_DIR = Path(__file__).resolve().parent / 'models_v2' / 'ner_model_vetbert'

print(f'  BASE       : {BASE}')
print(f'  OUTPUT_DIR : {OUTPUT_DIR}')

# Vérification que le dossier existe
if not BASE.exists():
    raise FileNotFoundError(
        f"Dossier data introuvable : {BASE}\n"
        f"Modifiez la variable BASE en haut du fichier."
    )

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────────────────────────
# LABELS
# ──────────────────────────────────────────────────────────────────
with open(BASE / 'ner_bio_labels.json', encoding='utf-8') as f:
    label_list = json.load(f)

label2id = {l: i for i, l in enumerate(label_list)}
id2label = {i: l for i, l in enumerate(label_list)}
print('Labels : ' + str(label_list))
print('Num labels : ' + str(len(label_list)))

# ──────────────────────────────────────────────────────────────────
# TOKENIZER
# ──────────────────────────────────────────────────────────────────
print('\nChargement tokenizer VetBERT...')
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)


# ──────────────────────────────────────────────────────────────────
# DATASET CLASS
# ──────────────────────────────────────────────────────────────────
class NERDataset(Dataset):
    def __init__(self, data_path, tokenizer, label2id, max_length=128):
        with open(data_path, encoding='utf-8') as f:
            self.data = json.load(f)
        self.tokenizer  = tokenizer
        self.label2id   = label2id
        self.max_length = max_length

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item   = self.data[idx]
        tokens = item['tokens']
        labels = item['ner_tags']

        encoding = self.tokenizer(
            tokens,
            is_split_into_words = True,
            max_length          = self.max_length,
            padding             = 'max_length',
            truncation          = True,
            return_tensors      = 'pt',
        )

        word_ids  = encoding.word_ids()
        label_ids = []
        prev_word = None

        for word_id in word_ids:
            if word_id is None:
                label_ids.append(-100)
            elif word_id != prev_word:
                label_ids.append(self.label2id.get(labels[word_id], self.label2id.get('O', 0)))
            else:
                lbl = labels[word_id]
                if lbl.startswith('B-'):
                    label_ids.append(self.label2id.get('I-' + lbl[2:], self.label2id.get('O', 0)))
                else:
                    label_ids.append(self.label2id.get(lbl, self.label2id.get('O', 0)))
            prev_word = word_id

        return {
            'input_ids'     : encoding['input_ids'].squeeze(),
            'attention_mask': encoding['attention_mask'].squeeze(),
            'labels'        : torch.tensor(label_ids, dtype=torch.long),
        }


# ──────────────────────────────────────────────────────────────────
# CHARGEMENT DATASETS
# ──────────────────────────────────────────────────────────────────
print('\nChargement datasets...')
train_dataset = NERDataset(BASE / 'ner_bio_train.json', tokenizer, label2id, max_length=128)
val_dataset   = NERDataset(BASE / 'ner_bio_val.json',   tokenizer, label2id, max_length=128)
test_dataset  = NERDataset(BASE / 'ner_bio_test.json',  tokenizer, label2id, max_length=128)

print('Train : ' + str(len(train_dataset)))
print('Val   : ' + str(len(val_dataset)))
print('Test  : ' + str(len(test_dataset)))


# ──────────────────────────────────────────────────────────────────
# CHARGEMENT VETBERT
# ──────────────────────────────────────────────────────────────────
print('\nChargement VetBERT...')
model = AutoModelForTokenClassification.from_pretrained(
    MODEL_NAME,
    num_labels              = len(label_list),
    id2label                = id2label,
    label2id                = label2id,
    ignore_mismatched_sizes = True,
)


# ──────────────────────────────────────────────────────────────────
# CLASS WEIGHTS
# ──────────────────────────────────────────────────────────────────
weights = []
for lbl in label_list:
    if lbl == 'O':
        weights.append(0.1)    # O très fréquent → poids faible
    elif lbl.startswith('B-'):
        weights.append(3.0)    # début entité → très important
    else:
        weights.append(2.0)    # I- continuation → important

class_weights = torch.tensor(weights, dtype=torch.float)
print('\nClass weights :')
for lbl, w in zip(label_list, weights):
    print('  ' + lbl + ' : ' + str(w))


# ──────────────────────────────────────────────────────────────────
# WEIGHTED TRAINER
# ──────────────────────────────────────────────────────────────────
class WeightedTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels  = inputs.get('labels')
        outputs = model(**inputs)
        logits  = outputs.get('logits')

        loss_fn = torch.nn.CrossEntropyLoss(
            weight       = class_weights.to(logits.device),
            ignore_index = -100,
        )
        loss = loss_fn(
            logits.view(-1, self.model.config.num_labels),
            labels.view(-1),
        )
        return (loss, outputs) if return_outputs else loss


# ──────────────────────────────────────────────────────────────────
# MÉTRIQUES
# ──────────────────────────────────────────────────────────────────
def compute_metrics(p):
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)

    true_labels = [
        [id2label[l] for l in label if l != -100]
        for label in labels
    ]
    true_preds = [
        [id2label[pred] for pred, l in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]

    return {
        'f1'       : f1_score(true_labels, true_preds),
        'precision': precision_score(true_labels, true_preds),
        'recall'   : recall_score(true_labels, true_preds),
    }


# ──────────────────────────────────────────────────────────────────
# TRAINING ARGUMENTS
# ──────────────────────────────────────────────────────────────────
training_args = TrainingArguments(
    output_dir                  = str(OUTPUT_DIR),
    num_train_epochs            = 4,
    per_device_train_batch_size = 16,
    per_device_eval_batch_size  = 16,
    learning_rate               = 2e-5,
    weight_decay                = 0.01,
    eval_strategy               = 'epoch',
    save_strategy               = 'epoch',
    load_best_model_at_end      = True,
    metric_for_best_model       = 'f1',
    logging_steps               = 50,
    warmup_steps                = 100,
    fp16                        = False,
    report_to                   = 'none',
    save_total_limit            = 2,
)

data_collator = DataCollatorForTokenClassification(tokenizer)

trainer = WeightedTrainer(
    model            = model,
    args             = training_args,
    train_dataset    = train_dataset,
    eval_dataset     = val_dataset,
    processing_class = tokenizer,
    data_collator    = data_collator,
    compute_metrics  = compute_metrics,
)


# ──────────────────────────────────────────────────────────────────
# ENTRAÎNEMENT
# ──────────────────────────────────────────────────────────────────
print('\nEntrainement VetBERT NER (4 epochs, max_length=128, class weights)...')
trainer.train()


# ──────────────────────────────────────────────────────────────────
# ÉVALUATION FINALE
# ──────────────────────────────────────────────────────────────────
print('\nEvaluation sur test set...')
predictions, labels, _ = trainer.predict(test_dataset)
predictions = np.argmax(predictions, axis=2)

true_labels = [
    [id2label[l] for l in label if l != -100]
    for label in labels
]
true_preds = [
    [id2label[pred] for pred, l in zip(prediction, label) if l != -100]
    for prediction, label in zip(predictions, labels)
]

print('\n' + '=' * 60)
print('RESULTATS VETBERT NER — Test Set')
print('=' * 60)
print(classification_report(true_labels, true_preds))

f1 = f1_score(true_labels, true_preds)
print('F1 macro : ' + str(round(f1, 4)))


# ──────────────────────────────────────────────────────────────────
# SAUVEGARDE
# ──────────────────────────────────────────────────────────────────
trainer.save_model(str(OUTPUT_DIR))
tokenizer.save_pretrained(str(OUTPUT_DIR))
print('\nModele sauvegarde : ' + str(OUTPUT_DIR))