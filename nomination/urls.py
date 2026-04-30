from django.urls import path
from .views import NominationView

urlpatterns = [
    path('', NominationView.as_view(), name='nomination-submit'),
]

