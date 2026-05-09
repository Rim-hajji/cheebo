import logging
import json
import os
import sys

# Ajout du chemin racine pour les imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from backend.nlp.pipeline import nlp_pipeline
from backend.agents.orchestrator import Orchestrator

# Configuration des logs
logging.basicConfig(level=logging.INFO)

def test_full_flow():
    print("\n" + "="*50)
    print("TEST DU FLUX COMPLET DES AGENTS (AVEC PREDICTION)")
    print("="*50)
    
    # Chargement de la KB
    kb_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "symptom_kb.json")
    with open(kb_path, 'r', encoding='utf-8') as f:
        kb_data = json.load(f)
    
    orchestrator = Orchestrator(kb_data)
    
    # Phrases de test
    test_phrases = [
        "Mon chien vomit depuis ce matin",
        "Ma chatte a la diarrhée",
        "Au secours, il fait des convulsions !",
        "Quel est le prix du vaccin ?"
    ]
    
    for phrase in test_phrases:
        print(f"\n- TEST : '{phrase}'")
        
        # 1. Pipeline NLP
        nlp_res = nlp_pipeline.process(phrase)
        
        # 2. Orchestration des agents
        final_result = orchestrator.handle(nlp_res)
        
        # 3. Affichage de la prédiction
        pred = final_result.get("results", {}).get("prediction", {})
        if pred:
            print(f"[PREDICTION AI] : {pred.get('prediction_summary')}")
            for t in pred.get('trajectoire', []):
                print(f"   TIME: {t}")
            print(f"   NOTE: {pred.get('note_theorique')}")
        else:
            print("Pas de prediction générée.")
            
        print("-" * 30)

if __name__ == "__main__":
    test_full_flow()
