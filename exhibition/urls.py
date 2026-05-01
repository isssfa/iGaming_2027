from django.urls import path
from .views import ExhibitionListAPIView, ExhibitorListAPIView

urlpatterns = [
    path('', ExhibitionListAPIView.as_view(), name='exhibition-list'),
    path('exhibitors/', ExhibitorListAPIView.as_view(), name='exhibitor-list'),
]