from django.urls import path

from .views import AffiliateRegisterPageView

urlpatterns = [
    path(
        'register/',
        AffiliateRegisterPageView.as_view(),
        name='affiliate-register-page',
    ),
]
