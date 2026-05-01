from django.urls import path
from .views import EventRegistrationView, InquiryView, PanelListView, TicketListView

urlpatterns = [
    path('register/', EventRegistrationView.as_view(), name='event-registration'),
    path('inquiry/', InquiryView.as_view(), name='inquiry'),
    path('schedule/', PanelListView.as_view(), name='panel-schedule'),
    path('tickets/', TicketListView.as_view(), name='ticket-list'),
]
