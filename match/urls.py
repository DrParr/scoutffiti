from django.urls import path
from .views import HomeView, EventDetailView, ScoutFormView

app_name = 'match'  # This is the namespace

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    # You can add more later, e.g.:
    # path('events/', views.event_list, name='event_list'),
    path('event/<str:event_key>/', EventDetailView.as_view(), name='event_detail'),
    path('scout/<str:match_key>/<str:alliance_color>/', ScoutFormView.as_view(), name='scout_form'),
    path('teams/', HomeView.as_view(), name='team_list'),
]