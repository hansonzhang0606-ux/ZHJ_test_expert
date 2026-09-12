@echo off
REM Sync local time tracking data to MySQL. A business line is mandatory.
set "BIZ_LINE=%~1"
if "%BIZ_LINE%"=="" (
  echo ERROR: business line is required. Pass it as the first argument.>> "%~dp0sync_log.txt"
  exit /b 2
)
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
set "PY_CMD="
where python >nul 2>&1 && set "PY_CMD=python"
if not defined PY_CMD if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PY_CMD if exist "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" set "PY_CMD=%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
if not defined PY_CMD (
  echo ERROR: Python 3.6+ was not found.>> "%~dp0sync_log.txt"
  exit /b 9009
)
"%PY_CMD%" sync_to_mysql.py --biz-line "%BIZ_LINE%" >> "%~dp0sync_log.txt" 2>&1
exit /b %ERRORLEVEL%