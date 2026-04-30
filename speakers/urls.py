from django.urls import path
from .views import SpeakerViewSet, BecomeASpeakerView

urlpatterns = [
    path('', SpeakerViewSet.as_view(), name='speaker-list'),
    path('become-a-speaker/', BecomeASpeakerView.as_view(), name='become-a-speaker'),
]