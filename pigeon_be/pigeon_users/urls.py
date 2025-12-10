from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from .views import AuthViewSet, UserViewSet

app_name = 'pigeon_users'


class NoSlashRouter(DefaultRouter):
    """Trailing slash를 제거하는 커스텀 라우터"""
    def __init__(self):
        super().__init__()
        self.trailing_slash = ''


router = NoSlashRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
    # JWT Token Refresh
    path('auth/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
]
