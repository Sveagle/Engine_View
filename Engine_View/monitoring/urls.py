"""URL configuration for monitoring application."""
from django.urls import path
from . import views

app_name = 'monitoring'

urlpatterns = [
    path('measurements/', views.measurement_list, name='measurement_list'),
    path('measurements/<int:pk>/', views.measurement_detail,
         name='measurement_detail'),
    path('trends/', views.trends, name='trends'),
    path('stats/', views.vessel_engine_stats, name='vessel_engine_stats'),
    path('measurements/create/', views.create_measurement,
         name='create_measurement'),
    path('api/chart-data/', views.chart_data_api, name='chart_data_api'),
    path('import-csv/', views.import_csv, name='import_csv'),
    path('download-template/', views.download_csv_template,
         name='download_csv_template'),
    path('measurements/<int:pk>/delete/', views.delete_measurement,
         name='delete_measurement'),
    path('parameters/', views.parameter_management,
         name='parameter_management'),
    path('parameters/<int:pk>/edit/', views.edit_parameter,
         name='edit_parameter'),
]
