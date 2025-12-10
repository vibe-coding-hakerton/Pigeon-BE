"""E2E 인증 API 테스트 스크립트"""
import requests
import json

BASE_URL = 'http://127.0.0.1:8000/v1/users'


def print_response(title, resp):
    print(f'\n{"="*50}')
    print(f'{title}')
    print(f'{"="*50}')
    print(f'Status: {resp.status_code}')
    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))


# 1. 이메일 중복체크 (사용 가능한 이메일)
resp = requests.post(f'{BASE_URL}/auth/check-email', json={
    'email': 'testuser@example.com'
})
print_response('1. 이메일 중복체크 (사용 가능)', resp)


# 2. 회원가입
resp = requests.post(f'{BASE_URL}/auth/signup', json={
    'username': 'testuser',
    'email': 'testuser@example.com',
    'password': 'TestPass123!',
    'password_confirm': 'TestPass123!',
    'gender': 'M',
    'birth_date': '1990-05-15',
    'phone_number': '010-1234-5678'
})
print_response('2. 회원가입', resp)


# 3. 이메일 중복체크 (이미 사용 중인 이메일)
resp = requests.post(f'{BASE_URL}/auth/check-email', json={
    'email': 'testuser@example.com'
})
print_response('3. 이메일 중복체크 (중복)', resp)


# 4. 로그인
resp = requests.post(f'{BASE_URL}/auth/login', json={
    'email': 'testuser@example.com',
    'password': 'TestPass123!'
})
print_response('4. 로그인', resp)

# 토큰 저장
if resp.status_code == 200:
    tokens = resp.json()['data']['tokens']
    refresh_token = tokens['refresh']
    access_token = tokens['access']
    print(f'\n>>> Access Token: {access_token[:50]}...')
    print(f'>>> Refresh Token: {refresh_token[:50]}...')

    # 5. 토큰 갱신
    resp = requests.post(f'{BASE_URL}/auth/token/refresh', json={
        'refresh': refresh_token
    })
    print_response('5. 토큰 갱신', resp)


# 6. 잘못된 비밀번호로 로그인 시도
resp = requests.post(f'{BASE_URL}/auth/login', json={
    'email': 'testuser@example.com',
    'password': 'WrongPassword!'
})
print_response('6. 로그인 실패 (잘못된 비밀번호)', resp)


# 7. 존재하지 않는 이메일로 로그인 시도
resp = requests.post(f'{BASE_URL}/auth/login', json={
    'email': 'notexist@example.com',
    'password': 'TestPass123!'
})
print_response('7. 로그인 실패 (존재하지 않는 이메일)', resp)

print('\n' + '='*50)
print('E2E 테스트 완료!')
print('='*50)
