"""Тесты для форм фильтрации измерений."""
from django.test import TestCase

from monitoring.forms import MeasurementFilterForm
from monitoring.models import Vessel, Engine


class FormTests(TestCase):
    """Тестирование форм фильтрации данных."""

    def setUp(self):
        """Создание тестовых данных."""
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

    def test_filter_form_valid(self):
        """Тест валидной формы с корректными данными."""
        form_data = {
            'vessel': self.vessel.id,
            'engine': self.engine.id,
            'date_from': '2024-01-01',
            'date_to': '2024-12-31'
        }
        form = MeasurementFilterForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_filter_form_invalid_dates(self):
        """Тест формы с невалидными датами."""
        form_data = {
            'date_from': 'invalid-date',
            'date_to': 'invalid-date'
        }
        form = MeasurementFilterForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_filter_form_empty(self):
        """Тест пустой формы (должна быть валидной)."""
        form = MeasurementFilterForm(data={})
        self.assertTrue(form.is_valid())

    def test_engine_queryset_filtering(self):
        """Тест фильтрации queryset двигателей по судну."""
        form_data = {'vessel': self.vessel.id}
        form = MeasurementFilterForm(data=form_data)
        form.is_valid()  # Триггерим обновление queryset

        # Двигатель должен быть в queryset так как принадлежит судну
        self.assertIn(self.engine, form.fields['engine'].queryset)
