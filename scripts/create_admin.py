#!/usr/bin/env python
"""관리자 계정 생성 스크립트"""

import os
import sys

# 프로젝트 경로 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'pigeon_be'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pigeon_be.settings')

import django
django.setup()

from pigeon_users.models import User

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='qwe123'
    )
    print('관리자 계정 생성 완료!')
    print('  - username: admin')
    print('  - password: qwe123')
else:
    print('admin 계정이 이미 존재합니다.')
