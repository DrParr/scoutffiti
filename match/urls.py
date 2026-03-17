from django.urls import path
from . import views

app_name = 'match'  # This is the namespace

urlpatterns = [
    path('', views.home, name='home'),
    # You can add more later, e.g.:
    # path('events/', views.event_list, name='event_list'),
    path('events/', views.home, name='event_list'),
    path('teams/', views.home, name='team_list'),
]