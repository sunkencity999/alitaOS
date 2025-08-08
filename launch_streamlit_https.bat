@echo off
setlocal ENABLEDELAYEDEXPANSION

REM AlitaOS Streamlit HTTPS Launch Script (Windows)
REM Generates a self-signed cert (with OpenSSL) and serves Streamlit over HTTPS (localhost)

cd /d "%~dp0"

echo 🔐 Starting AlitaOS over HTTPS (Streamlit)

REM Check .env
if not exist .env (
  echo ❌ .env not found. Please create it with OPENAI_API_KEY=...
  exit /b 1
)

REM Ensure Python
where python >nul 2>nul
if errorlevel 1 (
  echo ❌ Python not found. Install Python 3.10+ and ensure it's on PATH.
  exit /b 1
)

REM Create venv if missing
if not exist alitaOS\Scripts\activate.bat (
  echo 🔧 Creating virtual environment: alitaOS
  python -m venv alitaOS
)

call alitaOS\Scripts\activate.bat
python -m pip install --upgrade pip
if exist requirements.txt (
  pip install -r requirements.txt
)

REM Prepare cert directory
set CERT_DIR=.cert
if not exist %CERT_DIR% mkdir %CERT_DIR%
set CERT_FILE=%CERT_DIR%\cert.pem
set KEY_FILE=%CERT_DIR%\key.pem

REM Generate self-signed cert if missing (requires OpenSSL)
where openssl >nul 2>nul
if %errorlevel%==0 (
  if not exist "%CERT_FILE%" (
    echo 🪪 Generating self-signed TLS certificate (localhost)
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 ^
      -keyout "%KEY_FILE%" -out "%CERT_FILE%" ^
      -subj "/C=US/ST=CA/L=Local/O=AlitaOS/OU=Dev/CN=localhost"
  )
) else (
  echo ❗ OpenSSL not found on PATH.
  echo   - Option A: Install Git for Windows and ensure openssl.exe is on PATH.
  echo   - Option B: Install OpenSSL separately and add it to PATH.
  echo   - Option C: Use the HTTP launcher or run HTTPS via WSL using launch_streamlit_https.sh
  exit /b 1
)

cd app

echo 🌐 Open https://localhost:8501 (accept the browser warning)

REM Default realtime settings
if not defined ALITA_REALTIME_PORT set ALITA_REALTIME_PORT=8787
if not defined OPENAI_REALTIME_MODEL set OPENAI_REALTIME_MODEL=gpt-4o-realtime-preview-2024-12-17

echo 🎧 Starting realtime proxy TLS on https://localhost:%ALITA_REALTIME_PORT%
start "alita_realtime_proxy_tls" cmd /c python -m uvicorn app.realtime_proxy:app ^
  --host 127.0.0.1 ^
  --port %ALITA_REALTIME_PORT% ^
  --ssl-keyfile ..\%KEY_FILE% ^
  --ssl-certfile ..\%CERT_FILE%

streamlit run alita_streamlit.py ^
  --server.port 8501 ^
  --server.sslCertFile ..\%CERT_FILE% ^
  --server.sslKeyFile ..\%KEY_FILE%

ENDLOCAL
