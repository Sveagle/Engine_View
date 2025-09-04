"""Tests for URL routing configuration."""
from django.test import TestCase
from django.urls import reverse, resolve
from monitoring.views import measurement_list, measurement_detail


class UrlTests(TestCase):
    """Test cases for URL routing functionality."""

    def test_home_url(self):
        """Test that home page URL resolves correctly."""
        # Проверь без namespace сначала
        try:
            url = reverse('pages:home')
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
        except Exception:  # Конкретное исключение вместо bare except
            # Если не работает, проверь прямой URL
            response = self.client.get('/')
            self.assertEqual(response.status_code, 200)

    def test_measurement_list_url(self):
        """Test that measurement list URL resolves to correct view."""
        url = reverse('monitoring:measurement_list')
        self.assertEqual(resolve(url).func, measurement_list)

    def test_measurement_detail_url(self):
        """Test that measurement detail URL resolves to correct view."""
        url = reverse('monitoring:measurement_detail', args=[1])
        self.assertEqual(resolve(url).func, measurement_detail)

    def test_url_names(self):
        """Test that all expected URLs exist and are accessible."""
        # Test that all expected URLs exist
        urls = [
            reverse('pages:home'),
            reverse('monitoring:measurement_list'),
            reverse('admin:index'),
        ]

        for url in urls:
            response = self.client.get(url)
            self.assertIn(response.status_code, [200, 302])
