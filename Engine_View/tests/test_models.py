"""Тесты для моделей приложения monitoring."""
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from monitoring.models import Vessel, Engine, Measurement


class ModelTests(TestCase):
    """Тестирование моделей базы данных."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.vessel = Vessel.objects.create(
            name="Test Vessel",
            imo_number="IMO1234567"
        )
        self.engine = Engine.objects.create(
            vessel=self.vessel,
            name="Main Engine",
            model="ABC-123",
            serial_number="SN001"
        )

    def test_vessel_creation(self):
        """Тест создания модели судна."""
        self.assertEqual(self.vessel.name, "Test Vessel")
        self.assertEqual(self.vessel.imo_number, "IMO1234567")
        self.assertTrue(self.vessel.created_at)

    def test_engine_creation(self):
        """Тест создания модели двигателя."""
        self.assertEqual(self.engine.name, "Main Engine")
        self.assertEqual(self.engine.vessel, self.vessel)
        self.assertEqual(self.engine.serial_number, "SN001")

    def test_measurement_creation(self):
        """Тест создания модели замера."""
        measurement = Measurement.objects.create(
            engine=self.engine,
            timestamp=timezone.now(),
            temperature=85.5,
            pressure=15.2,
            rpm=1500
        )
        self.assertEqual(measurement.engine, self.engine)
        self.assertEqual(measurement.temperature, 85.5)
        self.assertEqual(measurement.pressure, 15.2)

    def test_measurement_validation(self):
        """Тест валидации некорректных значений замера."""
        measurement = Measurement(
            engine=self.engine,
            timestamp=timezone.now(),
            temperature=-100,  # Невалидная температура
            pressure=1000      # Невалидное давление
        )
        with self.assertRaises(ValidationError):
            measurement.full_clean()

    def test_string_representations(self):
        """Тест строкового представления моделей."""
        self.assertEqual(str(self.vessel), "Test Vessel")
        self.assertEqual(str(self.engine), "Main Engine (Test Vessel)")

        measurement = Measurement.objects.create(
            engine=self.engine,
            timestamp=timezone.now()
        )
        self.assertIn("Main Engine", str(measurement))
