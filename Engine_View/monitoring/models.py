from django.db import models
from django.contrib.auth.models import User


class Vessel(models.Model):
    name = models.CharField(max_length=100, verbose_name="Название судна")
    imo_number = models.CharField(max_length=20, unique=True, verbose_name="IMO номер")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Судно"
        verbose_name_plural = "Судна"

    def __str__(self):
        return self.name


class Engine(models.Model):
    vessel = models.ForeignKey(
        Vessel,
        on_delete=models.CASCADE,
        verbose_name="Судно",
        related_name="engines",
    )
    name = models.CharField(max_length=100, verbose_name="Название двигателя")
    model = models.CharField(max_length=50, verbose_name="Модель")
    serial_number = models.CharField(max_length=50, unique=True, verbose_name="Серийный номер")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Двигатель"
        verbose_name_plural = "Двигатели"

    def __str__(self):
        return f"{self.name} ({self.vessel.name})"


class ParameterType(models.Model):
    """Типы параметров, которые можно измерять"""
    UNIT_CHOICES = [
        ('°C', 'Градусы Цельсия'),
        ('бар', 'Бар'),
        ('об/мин', 'Обороты в минуту'),
        ('л/ч', 'Литр в час'),
        ('кПа', 'Килопаскаль'),
        ('%', 'Проценты'),
        ('л', 'Литр'),
        ('кг', 'Килограмм'),
        ('В', 'Вольт'),
        ('А', 'Ампер'),
        ('кВт', 'Киловатт'),
        ('кВт·ч', 'Киловатт-час'),
        ('дБ', 'Децибел'),
        ('мм', 'Миллиметр'),
        ('м/с', 'Метр в секунду'),
        ('', 'Без единиц'),
    ]

    name = models.CharField(max_length=100, verbose_name="Название параметра")
    code = models.SlugField(max_length=50, unique=True, verbose_name="Код параметра")
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, verbose_name="Единица измерения")
    description = models.TextField(blank=True, verbose_name="Описание")
    min_value = models.FloatField(null=True, blank=True, verbose_name="Минимальное значение")
    max_value = models.FloatField(null=True, blank=True, verbose_name="Максимальное значение")
    is_active = models.BooleanField(default=True, verbose_name="Активный")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Тип параметра"
        verbose_name_plural = "Типы параметров"

    def __str__(self):
        return f"{self.name} ({self.unit})"


class Measurement(models.Model):
    engine = models.ForeignKey(
        Engine,
        on_delete=models.CASCADE,
        verbose_name="Двигатель",
        related_name='measurements'
    )
    timestamp = models.DateTimeField(verbose_name="Время замера")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Кто добавил"
    )
    notes = models.TextField(blank=True, verbose_name="Примечания")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Замер"
        verbose_name_plural = "Замеры"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.engine} - {self.timestamp}"


class ParameterValue(models.Model):
    """Значения конкретных параметров для каждого замера"""
    measurement = models.ForeignKey(
        Measurement,
        on_delete=models.CASCADE,
        verbose_name="Замер",
        related_name='parameter_values'
    )
    parameter_type = models.ForeignKey(
        ParameterType,
        on_delete=models.CASCADE,
        verbose_name="Тип параметра"
    )
    value = models.FloatField(verbose_name="Значение")
    
    class Meta:
        verbose_name = "Значение параметра"
        verbose_name_plural = "Значения параметров"
        unique_together = ['measurement', 'parameter_type']

    def __str__(self):
        return f"{self.parameter_type.name}: {self.value} {self.parameter_type.unit}"