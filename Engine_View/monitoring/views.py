from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
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
    return render(request, 'monitoring/measurement_detail.html')
