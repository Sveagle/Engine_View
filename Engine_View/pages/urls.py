"""URL конфигурация для страниц."""
from django.urls import path
from pages import views

app_name = 'pages'

urlpatterns = [
    path('', views.home, name='home'),
    path('logout/success/', views.logout_success, name='logout_success'),
]
