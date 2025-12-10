from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from pigeon_commons.exceptions import (
    DuplicateEmailError,
    DuplicateUsernameError,
    EmailNotFoundError,
    PasswordMismatchError,
    CurrentPasswordError,
    InactiveAccountError,
    InvalidCredentialsError,
)

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """사용자 정보 시리얼라이저"""

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'gender',
            'birth_date',
            'phone_number',
            'date_joined',
        ]
        read_only_fields = ['id', 'date_joined']


class SignUpSerializer(serializers.ModelSerializer):
    """회원가입 시리얼라이저"""
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password],
    )
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password',
            'password_confirm',
            'gender',
            'birth_date',
            'phone_number',
        ]

    def validate_email(self, value):
        """이메일 중복 체크"""
        if User.objects.filter(email=value).exists():
            raise DuplicateEmailError()
        return value

    def validate_username(self, value):
        """유저네임 중복 체크"""
        if User.objects.filter(username=value).exists():
            raise DuplicateUsernameError()
        return value

    def validate(self, attrs):
        """비밀번호 확인 검증"""
        if attrs['password'] != attrs['password_confirm']:
            raise PasswordMismatchError()
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            gender=validated_data.get('gender'),
            birth_date=validated_data.get('birth_date'),
            phone_number=validated_data.get('phone_number'),
        )
        return user


class LoginSerializer(serializers.Serializer):
    """로그인 시리얼라이저"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        # 이메일로 사용자 찾기
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise EmailNotFoundError()

        # 비밀번호 확인
        if not user.check_password(password):
            raise InvalidCredentialsError()

        # 계정 활성화 확인
        if not user.is_active:
            raise InactiveAccountError()

        attrs['user'] = user
        return attrs

    def get_tokens(self, user):
        """JWT 토큰 생성"""
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class EmailCheckSerializer(serializers.Serializer):
    """이메일 중복 체크 시리얼라이저"""
    email = serializers.EmailField()

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise DuplicateEmailError()
        return value


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """프로필 수정 시리얼라이저 (username 변경 불가)"""

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'gender',
            'birth_date',
            'phone_number',
            'date_joined',
        ]
        read_only_fields = ['id', 'username', 'email', 'date_joined']


class PasswordChangeSerializer(serializers.Serializer):
    """비밀번호 변경 시리얼라이저"""
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password],
    )
    new_password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise CurrentPasswordError()
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise PasswordMismatchError('새 비밀번호가 일치하지 않습니다.')
        return attrs

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user
