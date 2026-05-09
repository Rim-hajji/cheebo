@echo off
REM Script d'installation de l'environnement Python pour module_docto_agent
REM Assurez-vous que Python 3.8+ est installé via Microsoft Store ou python.org

echo ========================================
echo Installation de l'environnement Python
echo ========================================

REM Vérifier si Python est installé
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo [ERREUR] Python n'est pas trouvé!
    echo.
    echo Solutions:
    echo 1. Installer Python depuis Microsoft Store:
    echo    - Ouvrir Microsoft Store
    echo    - Chercher "Python 3.11" (ou 3.10, 3.9)
    echo    - Cliquer sur "Installer"
    echo.
    echo 2. OU installer depuis python.org:
    echo    - Télécharger Python 3.11 depuis https://python.org
    echo    - Cocher "Add Python to PATH" pendant l'installation
    echo    - Redémarrer PowerShell après installation
    echo.
    echo Après installation, réexécutez ce script.
    pause
    exit /b 1
)

echo [OK] Python trouvé!
python --version

REM Créer l'environment virtuel
echo.
echo Création de l'environment virtuel...
if not exist venv (
    python -m venv venv
    echo [OK] Environment virtuel créé
) else (
    echo [OK] Environment virtuel existe déjà
)

REM Activer l'environment virtuel
echo.
echo Activation de l'environment virtuel...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERREUR] Impossible d'activer l'environment virtuel
    pause
    exit /b 1
)
echo [OK] Environment virtuel activé

REM Mettre à jour pip
echo.
echo Mise à jour de pip...
python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo [ERREUR] Impossible de mettre à jour pip
    pause
    exit /b 1
)
echo [OK] pip mis à jour

REM Installer les dépendances
echo.
echo Installation des dépendances...
echo Cette opération peut prendre 10-15 minutes (téléchargements importants)...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERREUR] Impossible d'installer les dépendances
    echo Essayez de réexécuter le script
    pause
    exit /b 1
)
echo [OK] Dépendances installées

REM Télécharger les modèles spaCy français
echo.
echo Téléchargement du modèle spaCy français...
python -m spacy download fr_core_news_sm
if %errorlevel% neq 0 (
    echo [AVERTISSEMENT] Impossible de télécharger fr_core_news_sm
    echo Le pipeline utilisera un modèle vierge (fallback)
)

echo.
echo ========================================
echo [SUCCESS] Installation terminée!
echo ========================================
echo.
echo Pour lancer l'entraînement, utilisez:
echo   python backend\nlp\train_all_models.py
echo.
echo L'environment virtuel est activé. Continuez vos commandes Python.
pause
