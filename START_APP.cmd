@echo off
cd /d "%~dp0"
python scripts\run.py --setup
if errorlevel 1 pause
