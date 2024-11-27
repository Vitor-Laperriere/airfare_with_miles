from django import forms
from django.core.exceptions import ValidationError
from datetime import date, timedelta
import re

class FlightSearchForm(forms.Form):
    origin = forms.CharField(
        label='Origem',
        max_length=3,
        min_length=3,
        widget=forms.TextInput(attrs={'placeholder': 'Ex.: GRU'}),
    )
    destination = forms.CharField(
        label='Destino',
        max_length=3,
        min_length=3,
        widget=forms.TextInput(attrs={'placeholder': 'Ex.: CGH'}),
    )
    date = forms.DateField(
        label='Data',
        widget=forms.DateInput(attrs={'type': 'date'}),
        input_formats=['%Y-%m-%d', '%d/%m/%Y']
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Define dinamicamente os valores de min e max no campo de data
        self.fields['date'].widget.attrs.update({
            'min': date.today().strftime('%Y-%m-%d'),
            'max': (date.today() + timedelta(days=329)).strftime('%Y-%m-%d'),
        })

    def clean_origin(self):
        origin = self.cleaned_data['origin'].upper()
        if not re.match(r'^[A-Z]{3}$', origin):
            raise ValidationError("O código da origem deve conter exatamente 3 letras (ex.: GRU).")
        return origin

    def clean_destination(self):
        destination = self.cleaned_data['destination'].upper()
        if not re.match(r'^[A-Z]{3}$', destination):
            raise ValidationError("O código do destino deve conter exatamente 3 letras (ex.: CGH).")
        return destination

    def clean_date(self):
        departure_date = self.cleaned_data['date']
        if departure_date < date.today():
            raise ValidationError("A data não pode ser no passado.")
        return departure_date