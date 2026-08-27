@echo off
REM Run from CIROH project root. Schedule this weekly (Task Scheduler).
cd /d "%~dp0"
python run_weekly_scan.py
exit /b %ERRORLEVEL%
