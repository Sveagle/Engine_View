"""
Views for Engine View monitoring system.
"""
import csv
import json
from datetime import datetime, timedelta
from io import TextIOWrapper

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CSVImportForm, MeasurementFilterForm, MeasurementWithParametersForm, ParameterTypeForm
from .models import Engine, Measurement, ParameterType, ParameterValue, Vessel


def home_view(request):
    """Главная страница системы мониторинга."""
    vessels = Vessel.objects.prefetch_related('engines').all()
    engines_count = Engine.objects.count()
    measurements_count = Measurement.objects.count()

    # Получаем дату последнего замера
    last_measurement = Measurement.objects.order_by('-timestamp').first()
    last_measurement_date = last_measurement.timestamp if last_measurement else None

    # Добавляем последний замер для каждого судна
    for vessel in vessels:
        vessel.last_measurement = Measurement.objects.filter(
            engine__vessel=vessel
        ).order_by('-timestamp').first()

    context = {
        'vessels': vessels,
        'vessels_count': vessels.count(),
        'engines_count': engines_count,
        'measurements_count': measurements_count,
        'last_measurement_date': last_measurement_date,
    }

    return render(request, 'monitoring/home.html', context)


def measurement_list(request):
    """
    Отображение списка всех замеров с возможностью фильтрации.

    Поддерживает фильтрацию по судну, двигателю и дате.
    """
    # Получаем все замеры с оптимизацией запросов
    measurements = Measurement.objects.select_related(
        'engine', 'engine__vessel', 'created_by'
    ).prefetch_related(
        'parameter_values__parameter_type'
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
    paginator = Paginator(measurements, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    one_week_ago = timezone.now() - timedelta(days=7)

    context = {
        'measurements': measurements,
        'vessels_count': measurements.values('engine__vessel').distinct().count(),
        'engines_count': measurements.values('engine').distinct().count(),
        'last_week_count': measurements.filter(timestamp__gte=one_week_ago).count(),
        'filter_form': filter_form,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': page_obj,
    }

    return render(request, 'monitoring/measurement_list.html', context)


def measurement_detail(request, pk):
    """Детальная страница просмотра конкретного замера."""
    measurement = get_object_or_404(
        Measurement.objects.select_related(
            'engine__vessel', 'created_by'
        ).prefetch_related('parameter_values__parameter_type'),
        pk=pk
    )

    # Группируем параметры для удобного отображения
    parameters = {}
    for param_value in measurement.parameter_values.all():
        parameters[param_value.parameter_type.name] = {
            'value': param_value.value,
            'unit': param_value.parameter_type.unit,
            'code': param_value.parameter_type.code,
        }

    return render(request, 'monitoring/measurement_detail.html', {
        'measurement': measurement,
        'parameters': parameters,
    })


def trends(request):
    """Страница с графиками трендов параметров двигателей."""
    vessels = Vessel.objects.all()
    engines = Engine.objects.all()
    parameter_types = ParameterType.objects.filter(is_active=True)

    # Фильтрация
    measurements = Measurement.objects.select_related(
        'engine__vessel'
    ).prefetch_related('parameter_values__parameter_type')

    vessel_id = request.GET.get('vessel')
    engine_id = request.GET.get('engine')
    parameter_code = request.GET.get('parameter')
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

    # Получаем выбранный параметр (без 404 ошибки)
    selected_parameter = None
    if parameter_code:
        try:
            selected_parameter = ParameterType.objects.get(code=parameter_code, is_active=True)
        except ParameterType.DoesNotExist:
            # Если параметр не найден, берем первый активный
            selected_parameter = parameter_types.first()
            messages.warning(request, f'Параметр "{parameter_code}" не найден. Показан первый доступный параметр.')
    else:
        # Если параметр не выбран, берем первый активный
        selected_parameter = parameter_types.first()

    # Подготовка данных для графиков
    chart_data = {}
    if selected_parameter and measurements.exists():
        chart_data = prepare_chart_data(measurements, selected_parameter)

    context = {
        'vessels': vessels,
        'engines': engines,
        'parameter_types': parameter_types,
        'selected_parameter': selected_parameter,
        'measurements_count': measurements.count(),
        'date_range': get_date_range_display(date_from, date_to),
        'vessels_count': vessels.count(),
        'engines_count': engines.count(),
        'chart_data_json': json.dumps(chart_data),
    }
    return render(request, 'monitoring/trends.html', context)


def prepare_chart_data(measurements, parameter_type):
    """
    Подготовка данных для построения графиков.

    Args:
        measurements: QuerySet замеров
        parameter_type: Тип параметра для отображения

    Returns:
        dict: Данные для графика
    """
    # Сортируем по времени
    measurements = measurements.order_by('timestamp')

    # Собираем значения для выбранного параметра
    labels = []
    values = []

    for measurement in measurements:
        # Ищем значение параметра для этого замера
        param_value = measurement.parameter_values.filter(
            parameter_type=parameter_type
        ).first()
        if param_value:
            labels.append(measurement.timestamp.strftime('%d.%m.%Y %H:%M'))
            values.append(float(param_value.value))

    return {
        'labels': labels,
        'values': values,
        'parameter_name': parameter_type.name,
        'parameter_unit': parameter_type.unit,
    }


def get_date_range_display(date_from, date_to):
    """Форматирование периода для отображения в интерфейсе."""
    if date_from and date_to:
        return f"{date_from} - {date_to}"
    elif date_from:
        return f"С {date_from}"
    elif date_to:
        return f"По {date_to}"
    return "Весь период"


def chart_data_api(request):
    """API endpoint для получения данных графиков в JSON формате."""
    vessel_id = request.GET.get('vessel')
    engine_id = request.GET.get('engine')
    parameter_code = request.GET.get('parameter', 'temperature')
    days = int(request.GET.get('days', 30))

    measurements = Measurement.objects.select_related(
        'engine__vessel'
    ).prefetch_related('parameter_values__parameter_type')

    if vessel_id:
        measurements = measurements.filter(engine__vessel_id=vessel_id)
    if engine_id:
        measurements = measurements.filter(engine_id=engine_id)

    date_from = datetime.now() - timedelta(days=days)
    measurements = measurements.filter(timestamp__gte=date_from)

    # Получаем параметр
    parameter_type = get_object_or_404(ParameterType, code=parameter_code)

    chart_data = prepare_chart_data(measurements, parameter_type)

    return JsonResponse(chart_data)


@login_required
def create_measurement(request):
    """Создание нового замера с динамическими параметрами."""
    if request.method == 'POST':
        form = MeasurementWithParametersForm(request.POST)
        if form.is_valid():
            measurement = form.save(commit=False)
            measurement.created_by = request.user
            measurement.save()

            # Сохраняем значения параметров
            active_parameters = ParameterType.objects.filter(is_active=True)
            for param in active_parameters:
                field_name = f'param_{param.code}'
                value = form.cleaned_data.get(field_name)
                if value is not None:  # сохраняем только если значение указано
                    ParameterValue.objects.create(
                        measurement=measurement,
                        parameter_type=param,
                        value=value,
                    )

            return redirect('monitoring:measurement_detail', pk=measurement.pk)
    else:
        form = MeasurementWithParametersForm()

    return render(request, 'monitoring/create_measurement.html', {'form': form})


@login_required
def import_csv(request):
    """Импорт данных замеров из CSV файла - умная версия."""
    parameter_types = ParameterType.objects.filter(is_active=True)
    import_errors = []

    if request.method == 'POST':
        form = CSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = form.cleaned_data['csv_file']
            vessel = form.cleaned_data['vessel']
            engine = form.cleaned_data['engine']
            timestamp_format = form.cleaned_data['timestamp_format']
            delimiter = form.cleaned_data['delimiter']

            try:
                # Читаем CSV файл
                csv_reader = TextIOWrapper(csv_file.file, encoding='utf-8')
                reader = csv.DictReader(csv_reader, delimiter=delimiter)

                imported_count = 0
                error_rows = []
                created_parameters = []  # Для отслеживания созданных параметров

                # Получаем все активные параметры для маппинга
                parameter_mapping = {}
                for param in parameter_types:
                    parameter_mapping[param.code.lower()] = param
                    parameter_mapping[param.name.lower()] = param

                for row_num, row in enumerate(reader, start=2):
                    try:
                        # Ищем колонку с временем
                        timestamp_str = None
                        time_keys = ['timestamp', 'time', 'время', 'дата', 'date']

                        for key in time_keys:
                            if key in row and row.get(key):
                                timestamp_str = row[key]
                                break

                        if not timestamp_str:
                            error_rows.append(f"Строка {row_num}: Не найдена колонка с временем")
                            continue

                        # Парсим время
                        timestamp = datetime.strptime(timestamp_str.strip(), timestamp_format)

                        # Создаем замер
                        measurement = Measurement(
                            engine=engine,
                            timestamp=timestamp,
                            created_by=request.user,
                        )
                        measurement.save()

                        # Обрабатываем все остальные колонки как параметры
                        param_count = 0
                        for header, value in row.items():
                            # Пропускаем колонки с временем и пустые значения
                            header_lower = header.lower().strip()
                            if (header_lower in time_keys or
                                not value or
                                not str(value).strip() or
                                str(value).strip().lower() in ['null', 'none', '']):
                                continue

                            value_str = str(value).strip()

                            # Ищем соответствующий параметр
                            param_type = None

                            if header_lower in parameter_mapping:
                                param_type = parameter_mapping[header_lower]
                            else:
                                # Определяем тип параметра по данным
                                data_type = 'text'  # по умолчанию текст
                                unit = ''

                                # Пробуем определить числовой параметр
                                try:
                                    float(value_str.replace(',', '.'))
                                    data_type = 'number'
                                    # Пытаемся угадать единицы измерения
                                    if any(word in header_lower for word in ['temp', 'temperature', 'темп']):
                                        unit = '°C'
                                    elif any(word in header_lower for word in ['press', 'pressure', 'давлен']):
                                        unit = 'бар'
                                    elif any(word in header_lower for word in ['rpm', 'оборот', 'speed']):
                                        unit = 'об/мин'
                                    elif any(word in header_lower for word in ['fuel', 'топлив']):
                                        unit = 'л/ч'
                                except ValueError:
                                    data_type = 'text'

                                # Создаем новый параметр
                                param_type, created = ParameterType.objects.get_or_create(
                                    name=header.title(),
                                    code=header_lower.replace(' ', '_').replace('-', '_'),
                                    defaults={
                                        'unit': unit,
                                        'description': f'Автоматически создан из импорта. Тип: {data_type}',
                                        'is_active': True,
                                    }
                                )
                                parameter_mapping[header_lower] = param_type
                                if created:
                                    created_parameters.append(param_type)

                            # Сохраняем значение параметра в зависимости от типа
                            try:
                                if param_type.unit:  # Если есть единицы измерения - значит число
                                    clean_value = value_str.replace(',', '.').strip()
                                    param_value = float(clean_value)
                                else:
                                    # Пробуем как число, если не получается - сохраняем как текст
                                    try:
                                        clean_value = value_str.replace(',', '.').strip()
                                        param_value = float(clean_value)
                                        # Если получилось, но параметр без единиц - обновляем параметр
                                        if not param_type.unit:
                                            param_type.unit = 'ед.'
                                            param_type.save()
                                    except ValueError:
                                        # Сохраняем как текст (но нам нужно число, поэтому пропускаем)
                                        error_rows.append(
                                            f"Строка {row_num}: Текстовое значение "
                                            f"'{value_str}' для параметра '{header}'"
                                        )
                                        continue

                                ParameterValue.objects.create(
                                    measurement=measurement,
                                    parameter_type=param_type,
                                    value=param_value,
                                )
                                param_count += 1

                            except ValueError:
                                error_rows.append(
                                    f"Строка {row_num}: Неверное значение "
                                    f"'{value_str}' для параметра '{header}'"
                                )

                        if param_count > 0:
                            imported_count += 1

                    except ValueError as e:
                        error_rows.append(f"Строка {row_num}: Ошибка формата времени - {str(e)}")
                    except Exception as e:
                        error_rows.append(f"Строка {row_num}: Неожиданная ошибка - {str(e)}")

                # Итоговое сообщение
                if imported_count > 0:
                    messages.success(
                        request,
                        f'✅ Успешно импортировано {imported_count} замеров!'
                    )
                    if created_parameters:
                        messages.info(
                            request,
                            f'📊 Создано новых параметров: {len(created_parameters)}'
                        )
                else:
                    messages.error(
                        request,
                        '❌ Не удалось импортировать ни одного замера'
                    )

                if error_rows:
                    messages.warning(
                        request,
                        f'⚠️ Найдено ошибок: {len(error_rows)}'
                    )
                    import_errors = error_rows[:10]

                    return render(request, 'monitoring/import_csv.html', {
                        'form': form,
                        'import_errors': import_errors,
                        'parameter_types': parameter_types,
                        'created_parameters': created_parameters,
                    })

                return redirect('monitoring:measurement_list')

            except (csv.Error, UnicodeDecodeError) as e:
                messages.error(request, f'❌ Ошибка чтения CSV файла: {str(e)}')
                return render(request, 'monitoring/import_csv.html', {
                    'form': form,
                    'import_errors': [f'Ошибка файла: {str(e)}'],
                    'parameter_types': parameter_types,
                })
        else:
            messages.error(request, '❌ Исправьте ошибки в форме')
    else:
        form = CSVImportForm()

    return render(request, 'monitoring/import_csv.html', {
        'form': form,
        'import_errors': import_errors,
        'parameter_types': parameter_types,
    })


@login_required
def download_csv_template(request):
    """Генерация и скачивание шаблона CSV файла для импорта."""
    # Создаем HttpResponse с заголовками для CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = (
        'attachment; filename="template_import.csv"'
    )

    writer = csv.writer(response)

    # Заголовки колонок
    headers = ['timestamp']
    active_parameters = ParameterType.objects.filter(is_active=True)
    for param in active_parameters:
        headers.append(param.code)

    writer.writerow(headers)

    # Пример данных
    example_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    writer.writerow([example_time, '75.5', '1.2', '1500', '45.3'])
    writer.writerow([example_time, '76.1', '1.3', '1520', '45.8'])

    return response


def vessel_engine_stats(request):
    """Страница статистики по судам и двигателям."""
    vessels = Vessel.objects.prefetch_related(
        'engines__measurements__parameter_values__parameter_type'
    )

    stats = []
    for vessel in vessels:
        vessel_stats = {
            'vessel': vessel,
            'engines_count': vessel.engines.count(),
            'measurements_count': Measurement.objects.filter(
                engine__vessel=vessel
            ).count(),
            'engines': [],
        }

        for engine in vessel.engines.all():
            engine_measurements = engine.measurements.all()
            last_measurement = engine_measurements.order_by('-timestamp').first()

            engine_stats = {
                'engine': engine,
                'measurements_count': engine_measurements.count(),
                'last_measurement': last_measurement,
            }
            vessel_stats['engines'].append(engine_stats)

        stats.append(vessel_stats)

    return render(request, 'monitoring/vessel_engine_stats.html', {
        'stats': stats,
    })


@login_required
def delete_measurement(request, pk):
    """Удаление замера."""
    measurement = get_object_or_404(Measurement, pk=pk)

    if request.method == 'POST':

        vessel_name = measurement.engine.vessel.name
        engine_name = measurement.engine.name
        timestamp = measurement.timestamp

        measurement.delete()

        messages.success(
            request,
            f'Замер от {timestamp} (судно {vessel_name}, двигатель {engine_name}) удален'
        )
        return redirect('monitoring:measurement_list')

    return render(request, 'monitoring/confirm_delete.html', {
        'measurement': measurement
    })


@login_required
def parameter_management(request):
    """Страница управления параметрами."""
    parameters = ParameterType.objects.all().order_by('is_active', 'name')

    if request.method == 'POST':
        # Обработка включения/выключения параметров
        parameter_id = request.POST.get('parameter_id')
        action = request.POST.get('action')

        if parameter_id and action:
            parameter = get_object_or_404(ParameterType, id=parameter_id)

            if action == 'toggle':
                parameter.is_active = not parameter.is_active
                parameter.save()
                status = 'включен' if parameter.is_active else 'выключен'
                messages.success(request, f'Параметр "{parameter.name}" {status}')
            elif action == 'delete':
                # Проверяем, используется ли параметр
                if parameter.parametervalue_set.exists():
                    messages.error(
                        request,
                        f'Нельзя удалить параметр "{parameter.name}" - он используется в замерах'
                    )
                else:
                    parameter_name = parameter.name
                    parameter.delete()
                    messages.success(request, f'Параметр "{parameter_name}" удален')

            return redirect('monitoring:parameter_management')

    return render(request, 'monitoring/parameter_management.html', {
        'parameters': parameters,
    })


@login_required
def edit_parameter(request, pk):
    """Редактирование параметра."""
    parameter = get_object_or_404(ParameterType, pk=pk)

    if request.method == 'POST':
        form = ParameterTypeForm(request.POST, instance=parameter)
        if form.is_valid():
            form.save()
            messages.success(request, f'Параметр "{parameter.name}" обновлен')
            return redirect('monitoring:parameter_management')
    else:
        form = ParameterTypeForm(instance=parameter)

    return render(request, 'monitoring/edit_parameter.html', {
        'form': form,
        'parameter': parameter,
    })
