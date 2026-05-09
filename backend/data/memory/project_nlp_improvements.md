---
name: NLP improvements April 2025
description: Summary of NLP model improvements to reach 0.7+ macro F1
type: project
---

Dataset augmented and training pipeline rebuilt to generalise better.

**Why:** Original datasets had only 1006 unique examples (intent) and class imbalance (INFO=29, SUIVI=11 vs URGENCE=1148). Models were overfitting (val accuracy=1.0).

**Changes made:**
- Deleted redundant files: finetune.py, train_quick.py, run_ner.py, augment_urgency_aggressive.py, rag_manager.py, scraper_test.py, data_consolidator.py, train_urgency.py, train_ner.py (~500 MB results/ folder also removed)
- New scraper (scraper.py): multi-source (Wamiz chiens + chats), offline synthetic fallback
- New augmentation (augment_dataset.py): synonym substitution, paraphrase templates, prefix/suffix injection, minority-class oversampling → intent 2076->4000, urgency 1006->3600
- Rebuilt train_all_models.py: CamemBERT (better for French), stratified splits, weighted cross-entropy, weight_decay=0.01 (was 0.4), dropout=0.1 (was 0.6), patience=3 (was 1), macro F1 target, per-class classification_report on test set

**How to apply:** Run augmentation then training:
  py backend/nlp/augment_dataset.py
  py backend/nlp/train_all_models.py --use-aug
