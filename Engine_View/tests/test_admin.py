"""Тесты для административного интерфейса."""
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone

from monitoring.models import Vessel, Engine, Measurement


class AdminTests(TestCase):
    """Тестирование функциональности админ-панели."""

    def setUp(self):
        """Подготовка тестовых данных и аутентификация."""
        self.client = Client()
        self.admin_user = get_user_model().objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='testpass123'
        )
        self.client.force_login(self.admin_user)

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
            timestamp=timezone.now()
        )

    def test_vessel_admin_list(self):
        """Тест отображения списка судов в админке."""
        url = reverse('admin:monitoring_vessel_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Vessel")

    def test_engine_admin_list(self):
        """Тест отображения списка двигателей в админке."""
        url = reverse('admin:monitoring_engine_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Main Engine")

    def test_measurement_admin_list(self):
        """Тест отображения списка замеров в админке."""
        url = reverse('admin:monitoring_measurement_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_admin_add_objects(self):
        """Тест добавления новых объектов через админку."""
        vessel_data = {
            'name': 'New Vessel',
            'imo_number': 'IMO7654321'
        }
        url = reverse('admin:monitoring_vessel_add')
        response = self.client.post(url, vessel_data)
        self.assertEqual(response.status_code, 302)  # Редирект после успеха

        self.assertEqual(Vessel.objects.count(), 2)
