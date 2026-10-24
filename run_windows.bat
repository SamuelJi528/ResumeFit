@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    where py >nul 2>nul
    if errorlevel 1 (
        python -m venv .venv
    ) else (
        py -3 -m venv .venv
    )
    if errorlevel 1 goto setup_error
)

".venv\Scripts\python.exe" -c "import sys; assert sys.version_info >= (3, 11), 'Python 3.11 or newer is required.'"
if errorlevel 1 goto setup_error

".venv\Scripts\python.exe" -c "import flask, requests, pydantic, pypdf, docx, dotenv" >nul 2>nul
if errorlevel 1 (
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto setup_error
)

if not exist ".env" copy ".env.example" ".env" >nul
echo.
echo ResumeFit website
echo Put your Gemini API key in .env if you have not configured it yet.
echo Open http://127.0.0.1:8000 in your browser after the server starts.
echo Press Ctrl+C to stop the server.
echo.
".venv\Scripts\python.exe" server.py
if errorlevel 1 goto setup_error
exit /b 0

:setup_error
echo.
echo Setup or launch failed. Follow the Run locally section in README.md.
pause
exit /b 1
