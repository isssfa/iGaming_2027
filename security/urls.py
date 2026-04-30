from django.urls import path
from .views import CSRFTokenView

app_name = 'security'

urlpatterns = [
    path('csrf-token/', CSRFTokenView.as_view(), name='csrf-token'),
]

