"""
URL configuration for pigeon_be project.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('v1/users/', include('pigeon_users.urls')),
]
