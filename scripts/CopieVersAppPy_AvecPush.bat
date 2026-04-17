@echo off
setlocal
chcp 65001 >nul

:: Se placer dans le dossier parent
cd /d %~dp0..

echo ============================
echo BUILD + PUSH V1
echo ============================

:: === Horodatage ===
for /f %%i in ('powershell -command "Get-Date -Format yyyy-MM-dd_HH-mm-ss"') do set timestamp=%%i

:: === Nom backup ===
set backup_name=appV1-dev-%timestamp%.py

:: === Création dossier backups si absent ===
if not exist backups (
    mkdir backups
)

:: === 1. Sync Git (safe) ===
echo.
echo [INFO] Synchronisation Git...
git pull origin main

if errorlevel 1 (
    echo [ERREUR] git pull échoué
    pause
    exit
)

:: === 2. Copie dev → prod ===
copy app_dev.py app.py >nul

:: === 3. Injection BUILD ===
powershell -Command "(Get-Content app.py) -replace 'APP_BUILD = \"DEV_BUILD\"', 'APP_BUILD = \"%timestamp%\"' | Set-Content app.py"

:: === 4. Sauvegarde ===
copy app.py backups\%backup_name% >nul

:: === Vérifications ===
if exist app.py (
    echo [OK] app.py mis à jour avec BUILD = %timestamp%
) else (
    echo [ERREUR] copie vers app.py échouée
)

if exist backups\%backup_name% (
    echo [OK] Backup : backups\%backup_name%
) else (
    echo [ERREUR] backup échoué
)

:: === 5. Push Git ===
echo.
echo [INFO] Envoi vers GitHub...

git add app.py
git commit -m "V1 build %timestamp%" >nul 2>&1
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