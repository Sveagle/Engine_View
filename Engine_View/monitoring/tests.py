from django.test import TestCase
from django.utils import timezone
from .models import Vessel, Engine, Measurement
from .forms import MeasurementFilterForm


class MeasurementTestCase(TestCase):
    def setUp(self):
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

    def test_measurement_creation(self):
        self.assertEqual(Measurement.objects.count(), 1)
        self.assertEqual(self.measurement.engine.vessel.name, "Test Vessel")

    def test_filter_form(self):
        form_data = {
            'vessel': self.vessel.id,
            'date_from': '2024-01-01'
        }
        form = MeasurementFilterForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_measurement_list_view(self):
        response = self.client.get('/monitoring/measurements/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Vessel")
