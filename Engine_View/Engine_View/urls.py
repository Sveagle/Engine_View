"""URL configuration for Engine_View project."""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('monitoring/', include('monitoring.urls')),
    path('', include('pages.urls')),
]
