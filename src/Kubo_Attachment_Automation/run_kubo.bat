@echo off
cd /d "%~dp0"
"%~dp0venv\Scripts\python.exe" run_kubo.py >> logs\task_kubo.log 2>&1
