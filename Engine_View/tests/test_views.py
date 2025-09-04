"""Тесты для представлений (views) приложения monitoring."""
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from monitoring.models import Vessel, Engine, Measurement


class ViewTests(TestCase):
    """Тестирование представлений приложения monitoring."""

    def setUp(self):
        """Подготовка тестовых данных."""
        self.client = Client()
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
        self.measurement = Measurement.objects.create(
            engine=self.engine,
            timestamp=timezone.now(),
            temperature=85.5,
            pressure=15.2,
            rpm=1500
        )

    def test_home_view(self):
        """Тест главной страницы."""
        response = self.client.get(reverse('pages:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Vessel")
        self.assertContains(response, "Main Engine")

    def test_measurement_list_view(self):
        """Тест страницы списка замеров."""
        response = self.client.get(reverse('monitoring:measurement_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "85.5")
        self.assertContains(response, "15.2")

    def test_measurement_list_filtering(self):
        """Тест фильтрации списка замеров."""
        # Тест фильтра по судну
        url = reverse('monitoring:measurement_list')
        url += f'?vessel={self.vessel.id}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        # Тест фильтра по дате
        url = reverse('monitoring:measurement_list')
        url += '?date_from=2024-01-01'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_measurement_detail_view(self):
        """Тест страницы деталей замера."""
        response = self.client.get(
            reverse('monitoring:measurement_detail',
                    args=[self.measurement.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "85.5")

    def test_measurement_detail_404(self):
        """Тест обработки 404 ошибки для несуществующего замера."""
        response = self.client.get(
            reverse('monitoring:measurement_detail', args=[999])
        )
        self.assertEqual(response.status_code, 404)
