from django.db.models import Count
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect
from django.contrib.auth import logout


from monitoring.models import Vessel, Engine, Measurement


def home(request):
    # Простой и надежный подход без сложных аннотаций
    vessels = Vessel.objects.all().prefetch_related('engines')

    # Аннотируем только количество двигателей
    vessels = vessels.annotate(engine_count=Count('engines'))

    # Получаем статистику отдельными запросами
    engines_count = Engine.objects.count()
    measurements_count = Measurement.objects.count()
    last_measurement = Measurement.objects.order_by('-timestamp').first()

    # Для последнего замера каждого судна - будем обрабатывать в шаблоне или отдельно
    context = {
        'vessels': vessels,
        'vessels_count': vessels.count(),
        'engines_count': engines_count,
        'measurements_count': measurements_count,
        'last_measurement_date': last_measurement.timestamp if last_measurement else None,
    }

    return render(request, 'pages/home.html', context)


@require_http_methods(["GET", "POST"])
def custom_logout(request):
    logout(request)
    return redirect('logout_success')


def logout_success(request):
    return render(request, 'registration/logout.html')
