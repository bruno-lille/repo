@echo off
setlocal
chcp 65001 >nul

:: Se placer dans le dossier parent
cd /d %~dp0..

:: === Horodatage ===
for /f %%i in ('powershell -command "Get-Date -Format yyyy-MM-dd_HH-mm-ss"') do set timestamp=%%i

:: === Nom backup ===
set backup_name=appV1-dev-%timestamp%.py

:: === Création dossier backups si absent ===
if not exist backups (
    mkdir backups
)

:: === Copie dev → prod ===
copy app_dev.py app.py >nul

:: === Injection du BUILD dans app.py ===
powershell -Command "(Get-Content app.py) -replace 'APP_BUILD = \"DEV_BUILD\"', 'APP_BUILD = \"%timestamp%\"' | Set-Content app.py"

:: === Sauvegarde ===
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

echo.
pause