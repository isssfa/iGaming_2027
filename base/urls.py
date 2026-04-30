from django.urls import path
from .views import EventRegistrationView, InquiryView

urlpatterns = [
    path('register/', EventRegistrationView.as_view(), name='event-registration'),
    path('inquiry/', InquiryView.as_view(), name='inquiry'),
]
