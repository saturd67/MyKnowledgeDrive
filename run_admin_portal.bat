@echo off
REM Go to the directory where this batch file is located
cd /d %~dp0

REM Activate the virtual environment
call .venv\Scripts\activate

REM Run the Python script
python admin_portal.py

pause
