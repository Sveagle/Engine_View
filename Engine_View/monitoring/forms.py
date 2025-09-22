from django import forms
from .models import Vessel, Engine, Measurement, ParameterType, ParameterValue


class ParameterTypeForm(forms.ModelForm):
    class Meta:
        model = ParameterType
        fields = ['name', 'code', 'unit', 'description', 'min_value', 'max_value', 'is_active']


class MeasurementForm(forms.ModelForm):
    class Meta:
        model = Measurement
        fields = ['engine', 'timestamp', 'notes']
        widgets = {
            'timestamp': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }


class ParameterValueForm(forms.ModelForm):
    class Meta:
        model = ParameterValue
        fields = ['parameter_type', 'value']



class MeasurementWithParametersForm(forms.ModelForm):
    class Meta:
        model = Measurement
        fields = ['engine', 'timestamp', 'notes']
        widgets = {
            'timestamp': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }),
            'engine': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Дополнительные заметки...'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        active_parameters = ParameterType.objects.filter(is_active=True)

        for param in active_parameters:
            field_name = f'param_{param.code}'

            self.fields[field_name] = forms.FloatField(
                required=False,
                label=f"{param.name} ({param.unit})",
                help_text=f"Диапазон: {param.min_value or 'нет'} - {param.max_value or 'нет'}",
                widget=forms.NumberInput(attrs={
                    'class': 'form-control',
                    'step': '0.01',
                    'placeholder': f'Введите значение {param.unit}'
                })
            )


class MeasurementFilterForm(forms.Form):
    vessel = forms.ModelChoiceField(
        queryset=Vessel.objects.all(),
        required=False,
        label="Судно",
        empty_label="Все суда"
    )
    engine = forms.ModelChoiceField(
        queryset=Engine.objects.all(),
        required=False,
        label="Двигатель",
        empty_label="Все двигатели"
    )
    date_from = forms.DateField(
        required=False,
        label="С даты",
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    date_to = forms.DateField(
        required=False,
        label="По дату",
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Динамически ограничиваем выбор двигателей в зависимости от выбранного судна
        if 'vessel' in self.data:
            try:
                vessel_id = int(self.data.get('vessel'))
                self.fields['engine'].queryset = Engine.objects.filter(vessel_id=vessel_id)
            except (ValueError, TypeError):
                pass


class CSVImportForm(forms.Form):
    csv_file = forms.FileField(
        label="CSV файл с данными",
        help_text="Поддерживаются только файлы с расширением .csv",
        widget=forms.FileInput(attrs={'accept': '.csv'})
    )
    vessel = forms.ModelChoiceField(
        queryset=Vessel.objects.all(),
        label="Судно",
        required=True
    )
    engine = forms.ModelChoiceField(
        queryset=Engine.objects.all(),
        label="Двигатель",
        required=True
    )
    timestamp_format = forms.ChoiceField(
        choices=[
            ('%Y-%m-%d %H:%M:%S', '2023-12-31 14:30:00'),
            ('%d.%m.%Y %H:%M', '31.12.2023 14:30'),
            ('%m/%d/%Y %H:%M', '12/31/2023 14:30'),
            ('%Y-%m-%d', '2023-12-31 (только дата)'),
        ],
        initial='%Y-%m-%d %H:%M:%S',
        label="Формат даты/времени"
    )
    delimiter = forms.ChoiceField(
        choices=[
            (',', 'Запятая (,)'),
            (';', 'Точка с запятой (;)'),
            ('\t', 'Табуляция (Tab)'),
        ],
        initial=',',
        label="Разделитель колонок"
    )

    def clean_csv_file(self):
        """Валидация CSV файла."""
        csv_file = self.cleaned_data.get('csv_file')

        if not csv_file:
            raise forms.ValidationError("Файл не выбран")

        # Проверяем расширение файла
        if not csv_file.name.endswith('.csv'):
            raise forms.ValidationError("Файл должен иметь расширение .csv")

        # Проверяем размер файла (макс 10MB)
        if csv_file.size > 10 * 1024 * 1024:
            raise forms.ValidationError("Размер файла не должен превышать 10MB")

        return csv_file


class ParameterTypeForm(forms.ModelForm):
    class Meta:
        model = ParameterType
        fields = ['name', 'code', 'unit', 'description', 'min_value', 'max_value', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_code(self):
        """Валидация кода параметра."""
        code = self.cleaned_data['code']
        if not code.replace('_', '').isalnum():
            raise forms.ValidationError("Код может содержать только буквы, цифры и подчеркивания")
        return code.lower()
