"""URL configuration for Engine_View project."""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include

from pages.views import custom_logout, logout_success

urlpatterns = [
    path('admin/', admin.site.urls),
    path('monitoring/', include('monitoring.urls')),
    path('logout/', custom_logout, name='logout'),
    path('logout/success/', logout_success, name='logout_success'),
    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html',
        redirect_authenticated_user=True,
    ), name='login'),
    path('', include('pages.urls')),
]
