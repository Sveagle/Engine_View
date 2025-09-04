from django import forms
from .models import Vessel, Engine
from django.utils import timezone

class MeasurementFilterForm(forms.Form):
    vessel = forms.ModelChoiceField(
        queryset=Vessel.objects.all(),
        required=False,
        empty_label="Все суда",
        label="Судно"
    )
    engine = forms.ModelChoiceField(
        queryset=Engine.objects.all(),
        required=False,
        empty_label="Все двигатели",
        label="Двигатель"
    )
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Дата с"
    )
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Дата по"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Динамически обновляем queryset для двигателей на основе выбранного судна
        if 'vessel' in self.data:
            try:
                vessel_id = int(self.data.get('vessel'))
                self.fields['engine'].queryset = Engine.objects.filter(vessel_id=vessel_id)
            except (ValueError, TypeError):
                pass