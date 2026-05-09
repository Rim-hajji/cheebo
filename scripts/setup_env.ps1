# Script d'installation PowerShell pour module_docto_agent
# Assurez-vous que Python 3.8+ est installé

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Installation de l'environnement Python" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Vérifier si Python est installé
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python trouvé: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERREUR] Python n'est pas trouvé!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Solutions:" -ForegroundColor Yellow
    Write-Host "1. Installer Python depuis Microsoft Store:" -ForegroundColor Yellow
    Write-Host "   - Ouvrir Microsoft Store" -ForegroundColor White
    Write-Host "   - Chercher 'Python 3.11' (ou 3.10, 3.9)" -ForegroundColor White
    Write-Host "   - Cliquer sur 'Installer'" -ForegroundColor White
    Write-Host ""
    Write-Host "2. OU installer depuis python.org:" -ForegroundColor Yellow
    Write-Host "   - Télécharger Python 3.11 depuis https://python.org" -ForegroundColor White
    Write-Host "   - Cocher 'Add Python to PATH' pendant l'installation" -ForegroundColor White
    Write-Host "   - Redémarrer PowerShell après installation" -ForegroundColor White
    Write-Host ""
    Write-Host "Après installation, réexécutez ce script." -ForegroundColor Yellow
    Read-Host "Appuyez sur Entrée pour continuer"
    exit 1
}

# Créer l'environment virtuel
Write-Host ""
Write-Host "Création de l'environment virtuel..." -ForegroundColor Cyan

if (-Not (Test-Path "venv")) {
    python -m venv venv
    Write-Host "[OK] Environment virtuel créé" -ForegroundColor Green
} else {
    Write-Host "[OK] Environment virtuel existe déjà" -ForegroundColor Green
}

# Activer l'environment virtuel
Write-Host ""
Write-Host "Activation de l'environment virtuel..." -ForegroundColor Cyan

& ".\venv\Scripts\Activate.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERREUR] Impossible d'activer l'environment virtuel" -ForegroundColor Red
    Write-Host ""
    Write-Host "Essayez de relancer PowerShell en tant qu'administrateur:" -ForegroundColor Yellow
    Write-Host "1. Windows Key + X" -ForegroundColor White
    Write-Host "2. Sélectionner 'Windows Terminal (Admin)'" -ForegroundColor White
    Write-Host "3. Réexécuter ce script" -ForegroundColor White
    Read-Host "Appuyez sur Entrée pour continuer"
    exit 1
}

Write-Host "[OK] Environment virtuel activé" -ForegroundColor Green

# Mettre à jour pip
Write-Host ""
Write-Host "Mise à jour de pip..." -ForegroundColor Cyan

python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERREUR] Impossible de mettre à jour pip" -ForegroundColor Red
    Read-Host "Appuyez sur Entrée pour continuer"
    exit 1
}

Write-Host "[OK] pip mis à jour" -ForegroundColor Green

# Installer les dépendances
Write-Host ""
Write-Host "Installation des dépendances..." -ForegroundColor Cyan
Write-Host "Cette opération peut prendre 10-15 minutes (téléchargements importants)..." -ForegroundColor Yellow

pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERREUR] Impossible d'installer les dépendances" -ForegroundColor Red
    Write-Host "Essayez de réexécuter le script" -ForegroundColor Yellow
    Read-Host "Appuyez sur Entrée pour continuer"
    exit 1
}

Write-Host "[OK] Dépendances installées" -ForegroundColor Green

# Télécharger les modèles spaCy français
Write-Host ""
Write-Host "Téléchargement du modèle spaCy français..." -ForegroundColor Cyan

python -m spacy download fr_core_news_sm
if ($LASTEXITCODE -ne 0) {
    Write-Host "[AVERTISSEMENT] Impossible de télécharger fr_core_news_sm" -ForegroundColor Yellow
    Write-Host "Le pipeline utilisera un modèle vierge (fallback)" -ForegroundColor Yellow
} else {
    Write-Host "[OK] Modèle spaCy téléchargé" -ForegroundColor Green
}

# Succès
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "[SUCCESS] Installation terminée!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pour lancer l'entraînement, utilisez:" -ForegroundColor Cyan
Write-Host "  python backend/nlp/train_all_models.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "L'environment virtuel est activé. Continuez vos commandes Python." -ForegroundColor Green
Write-Host ""
