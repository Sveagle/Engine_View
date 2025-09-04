from django.contrib import admin
from .models import Vessel, Engine, Measurement


@admin.register(Vessel)
class VesselAdmin(admin.ModelAdmin):
    list_display = ['name', 'imo_number', 'created_at']
    search_fields = ['name', 'imo_number']


@admin.register(Engine)
class EngineAdmin(admin.ModelAdmin):
    list_display = ['name', 'model', 'vessel', 'serial_number']
    list_filter = ['vessel', 'model']
    search_fields = ['name', 'model', 'serial_number']


@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'engine', 'temperature', 'pressure', 'rpm']
    list_filter = ['engine__vessel', 'engine', 'timestamp']
    date_hierarchy = 'timestamp'
    search_fields = ['engine__name', 'engine__vessel__name']
