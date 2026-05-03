@echo off
title Admin Import / Export

:: Se placer dans le dossier racine dvd-bluray
cd /d "%~dp0.."

echo Lancement de l'application admin...
echo.

REM 🔥 ouvre le navigateur après 2 secondes
start "" cmd /c "timeout /t 2 >nul & start http://127.0.0.1:5001"

REM 🔥 lancer le bon script
py -3.11 tools\Imp_Exp.py

echo.
echo Appuyez sur une touche pour fermer...
pause > nul