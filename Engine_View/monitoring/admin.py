from django.contrib import admin
from .models import Vessel, Engine, Measurement, ParameterType, ParameterValue


class ParameterValueInline(admin.TabularInline):
    """Отображение значений параметров внутри замера"""
    model = ParameterValue
    extra = 0
    readonly_fields = ['parameter_type', 'value']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False  # Запрещаем добавлять через админку (только через формы)


@admin.register(Vessel)
class VesselAdmin(admin.ModelAdmin):
    list_display = ['name', 'imo_number', 'created_at']
    search_fields = ['name', 'imo_number']
    list_per_page = 20


@admin.register(Engine)
class EngineAdmin(admin.ModelAdmin):
    list_display = ['name', 'model', 'vessel', 'serial_number', 'created_at']
    list_filter = ['vessel', 'model']
    search_fields = ['name', 'model', 'serial_number']
    list_select_related = ['vessel']
    list_per_page = 20


@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'engine', 'vessel_name', 'parameters_count', 'created_by', 'created_at']
    list_filter = ['engine__vessel', 'engine', 'timestamp']
    date_hierarchy = 'timestamp'
    search_fields = ['engine__name', 'engine__vessel__name', 'created_by__username']
    readonly_fields = ['created_by', 'created_at']
    list_select_related = ['engine', 'engine__vessel', 'created_by']
    inlines = [ParameterValueInline]
    list_per_page = 50

    def vessel_name(self, obj):
        return obj.engine.vessel.name
    vessel_name.short_description = 'Судно'
    vessel_name.admin_order_field = 'engine__vessel__name'

    def parameters_count(self, obj):
        return obj.parameter_values.count()
    parameters_count.short_description = 'Кол-во параметров'

    def save_model(self, request, obj, form, change):
        """Автоматически устанавливаем пользователя при создании"""
        if not change:  # Если объект создается, а не изменяется
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ParameterType)
class ParameterTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'unit', 'min_value', 'max_value', 'is_active', 'created_at']
    list_filter = ['unit', 'is_active']
    search_fields = ['name', 'code', 'description']
    list_editable = ['is_active', 'min_value', 'max_value']
    prepopulated_fields = {'code': ['name']}
    list_per_page = 20


@admin.register(ParameterValue)
class ParameterValueAdmin(admin.ModelAdmin):
    list_display = ['measurement', 'parameter_type', 'value', 'get_vessel', 'get_engine']
    list_filter = ['parameter_type', 'measurement__engine__vessel']
    search_fields = [
        'parameter_type__name',
        'measurement__engine__name',
        'measurement__engine__vessel__name'
    ]
    readonly_fields = ['measurement', 'parameter_type', 'value']
    list_select_related = ['measurement__engine__vessel', 'parameter_type']
    list_per_page = 50

    def get_vessel(self, obj):
        return obj.measurement.engine.vessel.name
    get_vessel.short_description = 'Судно'
    get_vessel.admin_order_field = 'measurement__engine__vessel__name'

    def get_engine(self, obj):
        return obj.measurement.engine.name
    get_engine.short_description = 'Двигатель'
    get_engine.admin_order_field = 'measurement__engine__name'

    def has_add_permission(self, request):
        return False  # Запрещаем добавление через админку

    def has_change_permission(self, request, obj=None):
        return False  # Запрещаем изменение через админку
