@echo off
setlocal
chcp 65001 >nul

:: 🔥 Se placer dans le dossier parent (dvd-bluray)
cd /d %~dp0..

echo ============================
echo 🚀 Lancement de l'application
echo ============================

:: 🧹 Kill anciens process Python
echo [INFO] Fermeture anciens processus Python...
taskkill /F /IM python.exe >nul 2>&1

:: 🔐 Variables environnement LOCAL
set ENV=DEV
set GITHUB_TOKEN=ton_token_ici

:: ▶️ Lancer app en arrière-plan
echo [INFO] Démarrage serveur Flask...
start "" python app.py

:: ⏳ Attente démarrage serveur
timeout /t 2 >nul

:: 🌐 Ouvrir navigateur sans cache (Chrome)
echo [INFO] Ouverture navigateur sans cache...
start "" chrome --incognito http://127.0.0.1:5000

:: (option Edge si Chrome absent)
:: start "" msedge --inprivate http://127.0.0.1:5000

echo.
echo ✅ Application lancée
echo.

pause