@echo off
REM Launch AlitaOS (Streamlit)
SETLOCAL ENABLEDELAYEDEXPANSION

cd /d "%~dp0"

echo ======================================
echo   🚀 Starting AlitaOS (Streamlit)
echo ======================================

IF NOT EXIST alitaOS (
  echo ❌ venv 'alitaOS' not found. Run install_windows.bat first.
  exit /b 1
)

IF NOT EXIST .env (
  echo ❌ .env file not found. Please create .env with OPENAI_API_KEY=...
  exit /b 1
)

call alitaOS\Scripts\activate.bat

echo 🔧 Upgrading pip and ensuring dependencies are installed...
python -m pip install --upgrade pip
IF EXIST requirements.txt (
  pip install -r requirements.txt
) ELSE (
  echo ⚠️ requirements.txt not found. Make sure dependencies are installed.
)

REM Default realtime settings
if not defined ALITA_REALTIME_PORT set ALITA_REALTIME_PORT=8787
if not defined OPENAI_REALTIME_MODEL set OPENAI_REALTIME_MODEL=gpt-4o-realtime-preview-2024-12-17

cd app

echo 🎧 Starting realtime proxy on http://localhost:%ALITA_REALTIME_PORT%
start "alita_realtime_proxy" cmd /c python -m uvicorn app.realtime_proxy:app --host 127.0.0.1 --port %ALITA_REALTIME_PORT%

echo 🌐 Opening Streamlit at http://localhost:8501
streamlit run alita_streamlit.py --server.port 8501
ENDLOCAL
