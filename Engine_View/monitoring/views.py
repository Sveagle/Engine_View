from datetime import datetime, timedelta
import json

from django.db.models import Avg, Max, Min
from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.http import JsonResponse

from .models import Measurement, Vessel, Engine
from .forms import MeasurementFilterForm


def measurement_list(request):
    # Получаем все замеры с оптимизацией запросов
    measurements = Measurement.objects.select_related(
        'engine', 'engine__vessel'
    ).order_by('-timestamp')

    # Применяем фильтры
    filter_form = MeasurementFilterForm(request.GET)

    if filter_form.is_valid():
        vessel = filter_form.cleaned_data.get('vessel')
        engine = filter_form.cleaned_data.get('engine')
        date_from = filter_form.cleaned_data.get('date_from')
        date_to = filter_form.cleaned_data.get('date_to')

        if vessel:
            measurements = measurements.filter(engine__vessel=vessel)
        if engine:
            measurements = measurements.filter(engine=engine)
        if date_from:
            measurements = measurements.filter(timestamp__date__gte=date_from)
        if date_to:
            measurements = measurements.filter(timestamp__date__lte=date_to)

    # Пагинация
    paginator = Paginator(measurements, 50)  # 50 записей на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'measurements': page_obj,
        'vessels': Vessel.objects.all(),
        'engines': Engine.objects.all(),
        'filter_form': filter_form,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': page_obj,
    }

    return render(request, 'monitoring/measurement_list.html', context)


def measurement_detail(request, pk):
    """Детальная страница замера"""
    # Получаем замер по ID или возвращаем 404
    measurement = get_object_or_404(Measurement.objects.select_related('engine__vessel'), pk=pk)

    return render(request, 'monitoring/measurement_detail.html', {
        'measurement': measurement
    })


def trends(request):
    """Страница с графиками трендов"""
    vessels = Vessel.objects.all()
    engines = Engine.objects.all()

    # Фильтрация
    measurements = Measurement.objects.all()

    vessel_id = request.GET.get('vessel')
    engine_id = request.GET.get('engine')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    if vessel_id:
        measurements = measurements.filter(engine__vessel_id=vessel_id)
    if engine_id:
        measurements = measurements.filter(engine_id=engine_id)
    if date_from:
        measurements = measurements.filter(timestamp__date__gte=date_from)
    if date_to:
        measurements = measurements.filter(timestamp__date__lte=date_to)

    # Подготовка данных для графиков
    chart_data = prepare_chart_data(measurements)

    context = {
        'vessels': vessels,
        'engines': engines,
        'measurements_count': measurements.count(),
        'date_range': get_date_range_display(date_from, date_to),
        'vessels_count': vessels.count(),
        'engines_count': engines.count(),
        'chart_data_json': json.dumps(chart_data),  # ← JSON для JavaScript
    }
    return render(request, 'monitoring/trends.html', context)

def prepare_chart_data(measurements):
    """Подготовка данных для графиков"""
    # Сортируем по времени
    measurements = measurements.order_by('timestamp')

    # Формируем данные
    labels = [m.timestamp.strftime('%d.%m.%Y %H:%M') for m in measurements]

    return {
        'labels': labels,
        'temperature': [float(m.temperature) if m.temperature else 0 for m in measurements],
        'pressure': [float(m.pressure) if m.pressure else 0 for m in measurements],
        'rpm': [float(m.rpm) if m.rpm else 0 for m in measurements],
        'fuel_consumption': [float(m.fuel_consumption) if m.fuel_consumption else 0 for m in measurements],
    }

def get_date_range_display(date_from, date_to):
    """Форматирование периода для отображения"""
    if date_from and date_to:
        return f"{date_from} - {date_to}"
    elif date_from:
        return f"С {date_from}"
    elif date_to:
        return f"По {date_to}"
    return "Весь период"

def chart_data_api(request):
    """API endpoint для получения данных графиков"""
    vessel_id = request.GET.get('vessel')
    engine_id = request.GET.get('engine')
    days = int(request.GET.get('days', 30))
    
    measurements = Measurement.objects.all()
    
    if vessel_id:
        measurements = measurements.filter(engine__vessel_id=vessel_id)
    if engine_id:
        measurements = measurements.filter(engine_id=engine_id)
    
    date_from = datetime.now() - timedelta(days=days)
    measurements = measurements.filter(timestamp__gte=date_from)
    
    chart_data = prepare_chart_data(measurements)
    
    return JsonResponse(chart_data)