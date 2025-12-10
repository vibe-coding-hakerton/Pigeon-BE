"""E2E 사용자 API 테스트 스크립트"""
import requests
import json

BASE_URL = 'http://127.0.0.1:8000/v1/users'


def print_response(title, resp):
    print(f'\n{"="*50}')
    print(f'{title}')
    print(f'{"="*50}')
    print(f'Status: {resp.status_code}')
    try:
        print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
    except:
        print(resp.text)


# 1. 로그인하여 토큰 획득
print('\n>>> 로그인하여 토큰 획득 중...')
resp = requests.post(f'{BASE_URL}/auth/login', json={
    'email': 'testuser@example.com',
    'password': 'TestPass123!'
})

if resp.status_code != 200:
    print('로그인 실패! 먼저 회원가입을 해주세요.')
    exit(1)

tokens = resp.json()['data']['tokens']
access_token = tokens['access']
headers = {'Authorization': f'Bearer {access_token}'}
print(f'>>> Access Token 획득 완료')


# 2. 내 정보 조회 (인증 없이 - 실패 테스트)
resp = requests.get(f'{BASE_URL}/me')
print_response('2. 내 정보 조회 (인증 없음 - 401 예상)', resp)


# 3. 내 정보 조회 (인증 있음)
resp = requests.get(f'{BASE_URL}/me', headers=headers)
print_response('3. 내 정보 조회 (인증 있음)', resp)


# 4. 내 정보 수정 (전화번호 변경)
resp = requests.patch(f'{BASE_URL}/me', headers=headers, json={
    'phone_number': '010-9999-8888',
    'gender': 'M'
})
print_response('4. 내 정보 수정 (전화번호 변경)', resp)


# 5. username 변경 시도 (변경 불가 확인)
resp = requests.patch(f'{BASE_URL}/me', headers=headers, json={
    'username': 'newusername'
})
print_response('5. username 변경 시도 (read_only - 무시됨)', resp)


# 6. 비밀번호 변경
resp = requests.post(f'{BASE_URL}/change-password', headers=headers, json={
    'current_password': 'TestPass123!',
    'new_password': 'NewPass456!',
    'new_password_confirm': 'NewPass456!'
})
print_response('6. 비밀번호 변경', resp)


# 7. 새 비밀번호로 로그인
resp = requests.post(f'{BASE_URL}/auth/login', json={
    'email': 'testuser@example.com',
    'password': 'NewPass456!'
})
print_response('7. 새 비밀번호로 로그인', resp)


# 8. 비밀번호 원복 (테스트용)
if resp.status_code == 200:
    new_tokens = resp.json()['data']['tokens']
    new_headers = {'Authorization': f'Bearer {new_tokens["access"]}'}
    
    resp = requests.post(f'{BASE_URL}/change-password', headers=new_headers, json={
        'current_password': 'NewPass456!',
        'new_password': 'TestPass123!',
        'new_password_confirm': 'TestPass123!'
    })
    print_response('8. 비밀번호 원복', resp)


# 9. 잘못된 현재 비밀번호로 변경 시도
resp = requests.post(f'{BASE_URL}/change-password', headers=headers, json={
    'current_password': 'WrongPassword!',
    'new_password': 'NewPass456!',
    'new_password_confirm': 'NewPass456!'
})
print_response('9. 비밀번호 변경 실패 (잘못된 현재 비밀번호)', resp)


print('\n' + '='*50)
print('사용자 API E2E 테스트 완료!')
print('='*50)
