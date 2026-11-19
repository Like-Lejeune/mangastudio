@echo off
rem Double-cliquez : range les fichiers du dossier a_ranger, puis vérifie le projet.
cd /d "%~dp0"
python ranger.py %*
echo.
python verifier_fichiers.py
echo.
pause
