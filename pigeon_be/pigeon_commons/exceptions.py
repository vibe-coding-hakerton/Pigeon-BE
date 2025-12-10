from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class ErrorCode:
    """
    에러 코드 정의

    코드 체계:
    - 10xxx: 공통 에러
    - 20xxx: 인증/인가 에러
    - 30xxx: 사용자 관련 에러
    - 40xxx: 유효성 검사 에러
    - 50xxx: 서버 에러
    """
    # 공통 에러 (10xxx)
    UNKNOWN_ERROR = '10000'
    BAD_REQUEST = '10001'
    NOT_FOUND = '10002'
    CONFLICT = '10003'

    # 인증/인가 에러 (20xxx)
    AUTHENTICATION_FAILED = '20000'
    INVALID_CREDENTIALS = '20001'
    INACTIVE_ACCOUNT = '20002'
    TOKEN_EXPIRED = '20003'
    TOKEN_INVALID = '20004'
    PERMISSION_DENIED = '20005'

    # 사용자 관련 에러 (30xxx)
    USER_NOT_FOUND = '30000'
    EMAIL_NOT_FOUND = '30001'
    DUPLICATE_EMAIL = '30002'
    DUPLICATE_USERNAME = '30003'

    # 유효성 검사 에러 (40xxx)
    VALIDATION_ERROR = '40000'
    PASSWORD_MISMATCH = '40001'
    CURRENT_PASSWORD_ERROR = '40002'
    INVALID_EMAIL_FORMAT = '40003'
    PASSWORD_TOO_WEAK = '40004'


class BaseAPIException(APIException):
    """기본 API 예외 클래스"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '요청 처리 중 오류가 발생했습니다.'
    default_code = ErrorCode.UNKNOWN_ERROR


class ValidationError(BaseAPIException):
    """유효성 검사 실패"""
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '입력값이 유효하지 않습니다.'
    default_code = ErrorCode.VALIDATION_ERROR


class AuthenticationError(BaseAPIException):
    """인증 실패"""
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = '인증에 실패했습니다.'
    default_code = ErrorCode.AUTHENTICATION_FAILED


class PermissionDeniedError(BaseAPIException):
    """권한 없음"""
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = '접근 권한이 없습니다.'
    default_code = ErrorCode.PERMISSION_DENIED


class NotFoundError(BaseAPIException):
    """리소스 없음"""
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = '요청한 리소스를 찾을 수 없습니다.'
    default_code = ErrorCode.NOT_FOUND


class ConflictError(BaseAPIException):
    """리소스 충돌 (중복 등)"""
    status_code = status.HTTP_409_CONFLICT
    default_detail = '리소스 충돌이 발생했습니다.'
    default_code = ErrorCode.CONFLICT


class DuplicateEmailError(ConflictError):
    """이메일 중복"""
    default_detail = '이미 사용 중인 이메일입니다.'
    default_code = ErrorCode.DUPLICATE_EMAIL


class DuplicateUsernameError(ConflictError):
    """사용자명 중복"""
    default_detail = '이미 사용 중인 사용자명입니다.'
    default_code = ErrorCode.DUPLICATE_USERNAME


class InvalidCredentialsError(AuthenticationError):
    """잘못된 인증 정보"""
    default_detail = '이메일 또는 비밀번호가 일치하지 않습니다.'
    default_code = ErrorCode.INVALID_CREDENTIALS


class EmailNotFoundError(NotFoundError):
    """이메일 없음"""
    default_detail = '등록되지 않은 이메일입니다.'
    default_code = ErrorCode.EMAIL_NOT_FOUND


class PasswordMismatchError(ValidationError):
    """비밀번호 불일치"""
    default_detail = '비밀번호가 일치하지 않습니다.'
    default_code = ErrorCode.PASSWORD_MISMATCH


class CurrentPasswordError(ValidationError):
    """현재 비밀번호 오류"""
    default_detail = '현재 비밀번호가 일치하지 않습니다.'
    default_code = ErrorCode.CURRENT_PASSWORD_ERROR


class InactiveAccountError(AuthenticationError):
    """비활성화 계정"""
    default_detail = '비활성화된 계정입니다.'
    default_code = ErrorCode.INACTIVE_ACCOUNT


def custom_exception_handler(exc, context):
    """
    커스텀 예외 핸들러

    DRF의 기본 예외 핸들러를 확장하여 일관된 응답 형식 제공
    """
    response = exception_handler(exc, context)

    if response is not None:
        error_detail = _extract_error_detail(exc, response.data)

        response.data = {
            'success': False,
            'data': None,
            'message': error_detail['message'],
            'errors': error_detail['errors'],
            'error_code': error_detail['code'],
        }

    return response


def _extract_error_detail(exc, data):
    """예외에서 에러 상세 정보 추출"""
    code = getattr(exc, 'default_code', ErrorCode.UNKNOWN_ERROR)

    if isinstance(exc, BaseAPIException):
        return {
            'message': str(exc.detail),
            'errors': None,
            'code': code,
        }

    if isinstance(data, dict):
        if 'detail' in data:
            return {
                'message': str(data['detail']),
                'errors': None,
                'code': code,
            }
        if 'non_field_errors' in data:
            return {
                'message': str(data['non_field_errors'][0]),
                'errors': data,
                'code': code,
            }
        first_error = _get_first_error_message(data)
        return {
            'message': first_error,
            'errors': data,
            'code': code,
        }

    return {
        'message': '요청 처리 중 오류가 발생했습니다.',
        'errors': data if data else None,
        'code': code,
    }


def _get_first_error_message(data):
    """딕셔너리에서 첫 번째 에러 메시지 추출"""
    for key, value in data.items():
        if isinstance(value, list) and value:
            return f'{key}: {value[0]}'
        elif isinstance(value, str):
            return f'{key}: {value}'
    return '요청 처리 중 오류가 발생했습니다.'
