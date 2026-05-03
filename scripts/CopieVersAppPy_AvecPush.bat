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

:: === Création dossier backups si absent ===
if not exist backups mkdir backups

:: === 1. Copie dev → prod ===
copy app_dev.py app.py >nul

:: === 2. Injection BUILD ===
powershell -Command "(Get-Content app.py) -replace 'APP_BUILD = \"DEV_BUILD\"', 'APP_BUILD = \"%timestamp%\"' | Set-Content app.py"

echo [OK] Build : %timestamp%

:: === TRACE BUILD ===
echo %timestamp% > last_build.txt

:: === 3. Backup local ===
copy app.py backups\%backup_name% >nul
echo [OK] Backup local : backups\%backup_name%

:: === 4. Git ===
echo.
echo [INFO] Push GitHub...

git status

git add app.py
git add .gitignore

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