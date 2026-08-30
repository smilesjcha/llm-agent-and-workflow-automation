@echo off
setlocal
cd /d "%~dp0\..\..\.."

if exist ".venv312\Scripts\python.exe" (
  set "DAY2_PYTHON=.venv312\Scripts\python.exe"
) else (
  where py >nul 2>nul
  if errorlevel 1 (
    echo Python 3.12를 찾지 못했습니다. 4차시 Python 환경을 먼저 확인해 주세요.
    pause
    exit /b 1
  )
  set "DAY2_PYTHON=py -3.12"
)

%DAY2_PYTHON% -c "import fastapi, multipart, pydantic, uvicorn" >nul 2>nul
if errorlevel 1 (
  echo Localhost 실행에 필요한 최소 Library를 최초 1회 설치합니다.
  %DAY2_PYTHON% -m pip install -r desktop-app\meeting-intelligence\requirements-localhost.txt
  if errorlevel 1 (
    pause
    exit /b 1
  )
)

%DAY2_PYTHON% scripts\run_day2_local_app.py
if errorlevel 1 pause
