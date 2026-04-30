from django.urls import path
from .views import ExhibitionListAPIView

urlpatterns = [
    path('', ExhibitionListAPIView.as_view(), name='exhibition-list'),
]