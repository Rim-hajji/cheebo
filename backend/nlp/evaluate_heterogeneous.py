import json
import torch
import numpy as np
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
import warnings
warnings.filterwarnings("ignore")

def load_data(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data

def evaluate_model(model_dir, data, task="intent"):
    print(f"\n--- Évaluation du modèle {task.upper()} sur le dataset Hétérogène ---")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    model.to(device)
    model.eval()
    
    texts = [d["text"] for d in data]
    true_labels = [d[task] for d in data]
    
    if task == "urgency":
        label_map = {"LOW": 0, "MODERATE": 1, "HIGH": 2, "CRITICAL": 3}
        true_labels = [label_map[l] if isinstance(l, str) else l for l in true_labels]
        target_names = ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    else:
        # Intent
        target_names = ["describe_symptom", "ask_advice", "emergency", "follow_up"]
        
    predictions = []
    batch_size = 32
    
    print(f"Évaluation sur {len(texts)} exemples...")
    
    with torch.no_grad():
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            inputs = tokenizer(batch_texts, padding=True, truncation=True, max_length=128, return_tensors="pt")
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            outputs = model(**inputs)
            preds = torch.argmax(outputs.logits, dim=1).cpu().numpy()
            predictions.extend(preds)
            
    # Calculate metrics
    acc = accuracy_score(true_labels, predictions)
    report = classification_report(true_labels, predictions, target_names=target_names)
    
    print(f"\nAccuracy: {acc:.4f}")
    print("\nClassification Report:")
    print(report)
    
    return acc, report

def main():
    # Chemins
    data_path = Path("../../dataset_builder/data_real/doctoagent_heterogeneous.json")
    
    if not data_path.exists():
        print(f"Erreur: Dataset introuvable ({data_path})")
        return
        
    data = load_data(data_path)
    
    # Évaluer Intent
    intent_model_dir = Path("models_v2/intent_model")
    if intent_model_dir.exists():
        evaluate_model(intent_model_dir, data, task="intent")
    else:
        print(f"\nModèle Intent introuvable ({intent_model_dir})")
        
    # Évaluer Urgency
    urgency_model_dir = Path("models_v2/urgency_model")
    if urgency_model_dir.exists():
        evaluate_model(urgency_model_dir, data, task="urgency")
    else:
        print(f"\nModèle Urgency introuvable ({urgency_model_dir})")

if __name__ == "__main__":
    main()
