from django.urls import path
from . import views

app_name = 'monitoring'

urlpatterns = [
    path('api/chart-data/', views.chart_data_api, name='chart_data_api'),
    path('<int:pk>/', views.measurement_detail, name='measurement_detail'),
    path('trends/', views.trends, name='trends'),
    path('', views.measurement_list, name='measurement_list'),
]
