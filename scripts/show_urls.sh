#!/bin/bash
# URL 확인 스크립트 (django-extensions 사용)
# 사용법: ./scripts/show_urls.sh

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/../pigeon_be"
PYTHON="C:/Users/Jaewan/.pyenv/pyenv-win/shims/python"

cd "$PROJECT_DIR"

echo "=== 등록된 URL 목록 ==="
echo ""
$PYTHON manage.py show_urls
