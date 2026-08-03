@echo off
cd /d "%~dp0"
py -3 START_HERE.py install 2>nul
if errorlevel 1 python START_HERE.py install
pause
