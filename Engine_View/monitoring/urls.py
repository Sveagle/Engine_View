from django.urls import path
from . import views

app_name = 'monitoring'

urlpatterns = [
    path('<int:pk>/', views.measurement_detail, name='measurement_detail'),
    path('', views.measurement_list, name='measurement_list'),
]
