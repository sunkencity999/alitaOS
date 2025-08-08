@echo off
REM AlitaOS Installer (Windows)
SETLOCAL ENABLEDELAYEDEXPANSION

echo 🚀 Installing AlitaOS (Streamlit)

REM Move to script directory
cd /d "%~dp0"

echo 📍 Working directory: %cd%

REM Ensure Python is available
where py >NUL 2>&1
IF ERRORLEVEL 1 (
  echo ❌ Python launcher not found. Please install Python 3.10+ from https://www.python.org/downloads/
  exit /b 1
)

REM Create venv named alitaOS if missing
IF NOT EXIST alitaOS (
  echo 🔧 Creating virtual environment: alitaOS
  py -m venv alitaOS
)

echo ✅ Virtual environment present

REM Activate and install deps
call alitaOS\Scripts\activate.bat
python -m pip install --upgrade pip
IF EXIST requirements.txt (
  echo 📦 Installing dependencies from requirements.txt
  pip install -r requirements.txt
) ELSE (
  echo ❌ requirements.txt not found. Aborting.
  exit /b 1
)

REM Ensure .env exists
IF NOT EXIST .env (
  echo 🔐 Creating .env template
  > .env echo OPENAI_API_KEY=
  echo ➡️  Please edit .env and set OPENAI_API_KEY.
)

echo ✅ Installation complete. To launch:
echo    launch_streamlit.bat
ENDLOCAL
