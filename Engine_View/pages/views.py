"""Views for the pages application."""
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect
from django.contrib.auth import logout

from monitoring.models import Vessel, Engine, Measurement


def home_view(request):
    """Главная страница"""
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

    return render(request, 'pages/home.html', context)


@require_http_methods(["GET", "POST"])
def custom_logout(request):
    """Выполняет выход пользователя из системы."""
    logout(request)
    return redirect('logout_success')


def logout_success(request):
    """Отображает страницу успешного выхода из системы."""
    return render(request, 'registration/logout.html')
