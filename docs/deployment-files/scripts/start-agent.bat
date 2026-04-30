@echo off
setlocal
set ROOT=%~dp0..
set AGENT_ROOT=%ROOT%\agent-src
set ENV_FILE=%ROOT%\config\agent\.env.demo
set PACKAGED_PYTHON=%ROOT%\agent-runtime\.venv\Scripts\python.exe
set EXTERNAL_PYTHON=E:\miniconda3\envs\suncaper\python.exe
set TARGET_ENV=%AGENT_ROOT%\.env

if exist "%ENV_FILE%" (
  copy /Y "%ENV_FILE%" "%TARGET_ENV%" >nul
  echo [agent] synced demo env to %TARGET_ENV%
)

if exist "%PACKAGED_PYTHON%" (
  if exist "%AGENT_ROOT%\main.py" (
    start "reviewpulse-agent" cmd /c "cd /d %AGENT_ROOT% && set DOTENV_PATH=%ENV_FILE% && "%PACKAGED_PYTHON%" main.py"
    echo [agent] started with bundled virtualenv
    exit /b 0
  )
)

if exist "%EXTERNAL_PYTHON%" (
  if exist "%AGENT_ROOT%\main.py" (
    start "reviewpulse-agent" cmd /c "cd /d %AGENT_ROOT% && set DOTENV_PATH=%ENV_FILE% && "%EXTERNAL_PYTHON%" main.py"
    echo [agent] started with external suncaper environment
    exit /b 0
  )
)

echo [agent] skipped: no usable python runtime found
echo [agent] checked:
echo   %PACKAGED_PYTHON%
echo   %EXTERNAL_PYTHON%
endlocal
