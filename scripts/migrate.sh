#!/bin/bash
# 마이그레이션 스크립트
# 사용법: ./scripts/migrate.sh [앱이름]

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/../pigeon_be"
PYTHON="C:/Users/Jaewan/.pyenv/pyenv-win/shims/python"

cd "$PROJECT_DIR"

if [ -z "$1" ]; then
    echo "=== 전체 마이그레이션 생성 ==="
    $PYTHON manage.py makemigrations
else
    echo "=== $1 앱 마이그레이션 생성 ==="
    $PYTHON manage.py makemigrations "$1"
fi

echo ""
echo "=== 마이그레이션 적용 ==="
$PYTHON manage.py migrate

echo ""
echo "=== 완료 ==="
