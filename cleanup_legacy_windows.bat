@echo off
REM Cleanup legacy Chainlit and unused files. Review before running.
SETLOCAL ENABLEDELAYEDEXPANSION

echo This will delete legacy Chainlit files. Continue? (Y/N)
set /p ANSW=
IF /I NOT "%ANSW%"=="Y" IF /I NOT "%ANSW%"=="YES" (
  echo Aborted.
  exit /b 1
)

REM Remove launcher and tests
if exist launch.bat del /f /q launch.bat
if exist launch_https.sh del /f /q launch_https.sh
if exist test_alitaos.py del /f /q test_alitaos.py
if exist test_alitaos_internal.py del /f /q test_alitaos_internal.py
if exist AUDIO_TROUBLESHOOTING.md del /f /q AUDIO_TROUBLESHOOTING.md

REM Remove Chainlit app files
if exist app\alita.py del /f /q app\alita.py
if exist app\.chainlit rd /s /q app\.chainlit
if exist app\realtime rd /s /q app\realtime

REM Remove chainlit mocks/tests
if exist app\scripts\test_tools rd /s /q app\scripts\test_tools

REM Optional: remove chainlit-based tools if not used by Streamlit
REM del /f /q app\tools\browser.py app\tools\email.py app\tools\linkedin.py app\tools\database.py

REM Docker references to Chainlit
if exist Dockerfile del /f /q Dockerfile

REM Remove stray Chainlit docs
if exist app\chainlit.md del /f /q app\chainlit.md

echo ✅ Cleanup complete.
ENDLOCAL
