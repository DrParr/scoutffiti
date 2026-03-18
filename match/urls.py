from django.urls import path
from .views import HomeView, EventDetailView

app_name = 'match'  # This is the namespace

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    # You can add more later, e.g.:
    # path('events/', views.event_list, name='event_list'),
    path('event/<str:event_key>/', EventDetailView.as_view(), name='event_detail'),
    path('teams/', HomeView.as_view(), name='team_list'),
]