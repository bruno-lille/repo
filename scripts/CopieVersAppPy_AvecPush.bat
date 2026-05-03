:: === CopieVersAppPy_AvecPush.bat ===

@echo off
setlocal
chcp 65001 >nul

cd /d %~dp0..

echo ============================
echo BUILD + PUSH V1
echo ============================

:: === Horodatage ===
for /f %%i in ('powershell -command "Get-Date -Format yyyy-MM-dd_HH-mm-ss"') do set timestamp=%%i

set backup_name=appV1-dev-%timestamp%.py

:: === Création dossier local_backups ===
if not exist local_backups mkdir local_backups

:: =========================================
:: 🔥 0. CLEAN AVANT PULL (IMPORTANT)
:: =========================================
echo.
echo [INFO] Nettoyage des changements locaux...

git add -A
git commit -m "auto-save before pull %timestamp%" >nul 2>&1

:: =========================================
:: 🔥 1. SYNC GITHUB
:: =========================================
echo.
echo [INFO] Sync avec GitHub...

git pull origin main --rebase

if errorlevel 1 (
    echo [ERREUR] git pull échoué
    pause
    exit /b
)

echo [OK] Repo à jour

:: =========================================
:: 🔥 2. BUILD
:: =========================================

copy app_dev.py app.py >nul

powershell -Command "(Get-Content app.py) -replace 'APP_BUILD = \"DEV_BUILD\"', 'APP_BUILD = \"%timestamp%\"' | Set-Content app.py"

echo [OK] Build : %timestamp%

echo %timestamp% > last_build.txt

copy app.py local_backups\%backup_name% >nul
echo [OK] Backup local : local_backups\%backup_name%

:: =========================================
:: 🔥 3. PUSH
:: =========================================

echo.
echo [INFO] Push GitHub...

git add app.py
git commit -m "V1 build %timestamp%"

git push origin main

if errorlevel 1 (
    echo [ERREUR] git push échoué
) else (
    echo [OK] PUSH OK
)

echo.
echo ============================
echo FIN
echo ============================

pause