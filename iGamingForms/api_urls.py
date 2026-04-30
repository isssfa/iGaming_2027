from django.urls import path, include

urlpatterns = [
    path('', include('base.urls')),
    path('sponsors/', include('sponsor.urls')),
    path('sponsorships/', include('sponsorship.urls')),
    path('exhibition/', include('exhibition.urls')),
    path('speakers/', include('speakers.urls')),
    path('nominations/', include('nomination.urls')),
    path('awards/', include('awards.urls')),
    path('affiliates/', include('affiliates.urls')),
    path('security/', include('security.urls')),
]