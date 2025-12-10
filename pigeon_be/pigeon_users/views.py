from django.contrib.auth import get_user_model
from rest_framework import status, viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from pigeon_commons.permissions import IsOwner
from .serializers import (
    UserSerializer,
    SignUpSerializer,
    LoginSerializer,
    EmailCheckSerializer,
    ProfileUpdateSerializer,
    PasswordChangeSerializer,
)

User = get_user_model()


class AuthViewSet(viewsets.GenericViewSet):
    """인증 관련 ViewSet"""
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'signup':
            return SignUpSerializer
        elif self.action == 'login':
            return LoginSerializer
        elif self.action == 'check_email':
            return EmailCheckSerializer
        return UserSerializer

    @action(detail=False, methods=['post'])
    def signup(self, request):
        """회원가입"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                'success': True,
                'data': UserSerializer(user).data,
                'message': '회원가입이 완료되었습니다.',
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['post'])
    def login(self, request):
        """로그인"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        tokens = serializer.get_tokens(user)

        return Response(
            {
                'success': True,
                'data': {
                    'user': UserSerializer(user).data,
                    'tokens': tokens,
                },
                'message': '로그인에 성공했습니다.',
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['post'], url_path='check-email')
    def check_email(self, request):
        """이메일 중복 체크"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            {
                'success': True,
                'data': {'available': True},
                'message': '사용 가능한 이메일입니다.',
            },
            status=status.HTTP_200_OK,
        )


class UserViewSet(viewsets.GenericViewSet):
    """사용자 정보 ViewSet (JWT 인증 필요)"""
    permission_classes = [IsAuthenticated, IsOwner]
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == 'change_password':
            return PasswordChangeSerializer
        elif self.action in ['me', 'update_me']:
            return ProfileUpdateSerializer
        return UserSerializer

    @action(detail=False, methods=['get'])
    def me(self, request):
        """내 정보 조회"""
        serializer = self.get_serializer(request.user)
        return Response(
            {
                'success': True,
                'data': serializer.data,
                'message': '내 정보를 조회했습니다.',
            },
            status=status.HTTP_200_OK,
        )

    @me.mapping.patch
    def update_me(self, request):
        """내 정보 수정 (username, email 변경 불가)"""
        serializer = self.get_serializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                'success': True,
                'data': serializer.data,
                'message': '내 정보가 수정되었습니다.',
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['post'], url_path='change-password')
    def change_password(self, request):
        """비밀번호 변경"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {
                'success': True,
                'data': None,
                'message': '비밀번호가 변경되었습니다.',
            },
            status=status.HTTP_200_OK,
        )
