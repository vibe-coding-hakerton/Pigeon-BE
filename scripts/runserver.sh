#!/bin/bash
# 개발 서버 실행 스크립트
# 사용법: ./scripts/runserver.sh [포트]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/../pigeon_be"
PYTHON="C:/Users/Jaewan/.pyenv/pyenv-win/shims/python"

PORT=${1:-8000}

cd "$PROJECT_DIR"

echo "=== Django 개발 서버 실행 ==="
echo "URL: http://127.0.0.1:$PORT/"
echo "Admin: http://127.0.0.1:$PORT/admin/"
echo ""
$PYTHON manage.py runserver $PORT
