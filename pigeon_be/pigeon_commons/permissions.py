from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    객체의 소유자만 접근 가능한 권한
    사용자 본인만 자신의 정보에 접근할 수 있도록 함
    """
    message = '본인만 접근할 수 있습니다.'

    def has_object_permission(self, request, view, obj):
        # 객체가 User 모델인 경우
        if hasattr(obj, 'id') and hasattr(request.user, 'id'):
            return obj.id == request.user.id
        # 객체에 user 필드가 있는 경우
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    객체의 소유자는 모든 작업 가능, 그 외에는 읽기만 가능
    """
    message = '수정 권한이 없습니다.'

    def has_object_permission(self, request, view, obj):
        # 읽기 권한은 모두에게 허용
        if request.method in permissions.SAFE_METHODS:
            return True

        # 쓰기 권한은 소유자에게만 허용
        if hasattr(obj, 'id') and hasattr(request.user, 'id'):
            return obj.id == request.user.id
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False
