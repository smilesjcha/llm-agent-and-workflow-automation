#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPOSITORY_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"

if [[ -x "${REPOSITORY_ROOT}/.venv312/bin/python" ]]; then
  PYTHON_BIN="${REPOSITORY_ROOT}/.venv312/bin/python"
elif command -v python3.12 >/dev/null 2>&1; then
  PYTHON_BIN="$(command -v python3.12)"
else
  echo "Python 3.12를 찾지 못했습니다. 4차시 Python 환경을 먼저 확인해 주세요." >&2
  read -r -p "Enter를 누르면 닫힙니다."
  exit 1
fi

cd "${REPOSITORY_ROOT}"
if ! "${PYTHON_BIN}" -c "import fastapi, multipart, pydantic, uvicorn" >/dev/null 2>&1; then
  echo "Localhost 실행에 필요한 최소 Library를 최초 1회 설치합니다."
  "${PYTHON_BIN}" -m pip install -r desktop-app/meeting-intelligence/requirements-localhost.txt
fi
exec "${PYTHON_BIN}" scripts/run_day2_local_app.py
