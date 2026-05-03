@echo off
setlocal
chcp 65001 >nul

:: Se placer dans le dossier parent
cd /d %~dp0..

echo ============================
echo BUILD LOCAL (SAFE)
echo ============================

:: === Horodatage ===
for /f %%i in ('powershell -command "Get-Date -Format yyyy-MM-dd_HH-mm-ss"') do set timestamp=%%i

:: === Nom backup ===
set backup_name=appV1-dev-%timestamp%.py

:: === Création dossier local_backups si absent ===
if not exist local_backups (
    mkdir local_backups
)

:: === Copie dev → prod ===
copy app_dev.py app.py >nul

:: === Injection du BUILD dans app.py ===
powershell -Command "(Get-Content app.py) -replace 'APP_BUILD = \"DEV_BUILD\"', 'APP_BUILD = \"%timestamp%\"' | Set-Content app.py"

:: === Sauvegarde locale ===
copy app.py local_backups\%backup_name% >nul

:: === Vérifications ===
if exist app.py (
    echo [OK] app.py mis à jour avec BUILD = %timestamp%
) else (
    echo [ERREUR] copie vers app.py échouée
)

if exist local_backups\%backup_name% (
    echo [OK] Backup local : local_backups\%backup_name%
) else (
    echo [ERREUR] backup échoué
)

echo.
echo ============================
echo FIN
echo ============================

pause