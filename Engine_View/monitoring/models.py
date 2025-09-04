from django.db import models


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


class Measurement(models.Model):
    engine = models.ForeignKey(
        Engine,
        on_delete=models.CASCADE,
        verbose_name="Двигатель",
        related_name='measurements'
        )
    timestamp = models.DateTimeField(verbose_name="Время замера")

    # Основные параметры (примерные - нужно уточнить у препода)
    temperature = models.FloatField(null=True, blank=True, verbose_name="Температура, °C")
    pressure = models.FloatField(null=True, blank=True, verbose_name="Давление, бар")
    rpm = models.FloatField(null=True, blank=True, verbose_name="Обороты, об/мин")
    fuel_consumption = models.FloatField(null=True, blank=True, verbose_name="Расход топлива, л/ч")
    oil_pressure = models.FloatField(null=True, blank=True, verbose_name="Давление масла, бар")
    coolant_temperature = models.FloatField(null=True, blank=True, verbose_name="Температура охлаждающей жидкости, °C")

    # Добавить остальные ~25 параметров после получения структуры Excel

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Замер"
        verbose_name_plural = "Замеры"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.engine} - {self.timestamp}"
