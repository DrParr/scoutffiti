from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Standard Login/Logout views
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # This includes all URLs from the matches app
    # If you leave the first argument as '', it lives at the root (e.g., /)
    path('', include('match.urls')), 
]