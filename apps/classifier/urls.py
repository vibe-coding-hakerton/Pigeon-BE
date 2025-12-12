from django.urls import path

from . import views

app_name = 'classifier'

urlpatterns = [
    path('classify/', views.ClassifyView.as_view(), name='classify'),
    path('classify-unclassified/', views.ClassifyUnclassifiedView.as_view(), name='classify-unclassified'),
    path('<str:classification_id>/', views.ClassificationStatusView.as_view(), name='classification-status'),
    path('<str:classification_id>/stop/', views.ClassificationStopView.as_view(), name='classification-stop'),
]
