@echo off
title Admin Import / Export

echo Lancement de l'application admin...
echo.

cd /d "%~dp0"

py -3.11 imp-exp.py

echo.
echo Appuyez sur une touche pour fermer...
pause > nul