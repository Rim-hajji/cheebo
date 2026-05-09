
@echo off
echo ==========================================
echo 🐾 CHEEBO AI - DATA PIPELINE 🐾
echo ==========================================
echo 1/5 - Generation des donnees synthetiques...
py backend/data/generate_big_dataset.py
echo 2/5 - Scraping des donnees reelles (Wamiz)...
py backend/data/scraper.py
echo 3/5 - Chargement des datasets Hugging Face...
py backend/data/hf_loader.py
echo 4/5 - Consolidation du Master Dataset...
py backend/data/data_consolidator.py
echo 5/5 - Pretraitement spaCy / NLTK...
py backend/data/data_processor.py
echo ==========================================
echo ✅ PIPELINE TERMINEE ! 
echo Vous pouvez maintenant lancer start_training.bat
pause
