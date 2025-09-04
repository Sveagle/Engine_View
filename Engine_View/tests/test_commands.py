"""Тесты для кастомных management команд."""
import os
import tempfile
from io import StringIO

import pandas as pd
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from monitoring.models import Vessel, Engine, Measurement


class ImportCommandTests(TestCase):
    """Тестирование команды импорта данных из Excel."""

    def create_test_excel(self):
        """Создает тестовый Excel файл для импорта."""
        data = {
            'vessel_name': ['Test Vessel'],
            'imo_number': ['IMO1234567'],
            'engine_name': ['Main Engine'],
            'engine_model': ['ABC-123'],
            'serial_number': ['SN001'],
            'timestamp': ['2024-01-01 12:00:00'],
            'temperature': [85.5],
            'pressure': [15.2],
            'rpm': [1500]
        }

        df = pd.DataFrame(data)
        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        df.to_excel(temp_file.name, index=False)
        temp_file.close()
        return temp_file.name

    def tearDown(self):
        """Очистка временных файлов после тестов."""
        for file in os.listdir(tempfile.gettempdir()):
            if file.startswith('tmp') and file.endswith('.xlsx'):
                try:
                    os.unlink(os.path.join(tempfile.gettempdir(), file))
                except OSError:
                    pass

    def test_import_command_success(self):
        """Тест успешного импорта данных из Excel."""
        excel_file = self.create_test_excel()

        out = StringIO()
        call_command('import_measurements', excel_file, stdout=out)

        # Проверяем что данные импортировались
        self.assertEqual(Vessel.objects.count(), 1)
        self.assertEqual(Engine.objects.count(), 1)
        self.assertEqual(Measurement.objects.count(), 1)

        # Очистка
        os.unlink(excel_file)

    def test_import_command_file_not_found(self):
        """Тест обработки ошибки когда файл не найден."""
        with self.assertRaises(CommandError):
            call_command('import_measurements', 'nonexistent.xlsx')

    def test_import_command_invalid_file(self):
        """Тест обработки невалидного файла."""
        # Создаем невалидный файл
        temp_file = tempfile.NamedTemporaryFile(suffix='.txt', delete=False)
        temp_file.write(b'invalid content')
        temp_file.close()

        with self.assertRaises(CommandError):
            call_command('import_measurements', temp_file.name)

        os.unlink(temp_file.name)

    def test_import_command_missing_columns(self):
        """Тест обработки отсутствующих обязательных колонок."""
        # Создаем Excel без обязательных колонок
        data = {'wrong_column': ['test']}
        df = pd.DataFrame(data)

        temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        df.to_excel(temp_file.name, index=False)
        temp_file.close()

        with self.assertRaises(CommandError):
            call_command('import_measurements', temp_file.name)

        os.unlink(temp_file.name)
