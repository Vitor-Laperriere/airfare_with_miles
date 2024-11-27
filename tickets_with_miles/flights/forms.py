from django import forms
from django.core.exceptions import ValidationError
from datetime import date, timedelta

class FlightSearchForm(forms.Form):
    origin = forms.CharField(label='Origem', max_length=3)
    destination = forms.CharField(label='Destino', max_length=3)
    date = forms.DateField(
        label='Data',
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'min': date.today().strftime('%Y-%m-%d'),
                'max': (date.today() + timedelta(days=329)).strftime('%Y-%m-%d')
            }
        )
    )

    def clean_date(self):
        departure_date = self.cleaned_data['date']
        if departure_date < date.today():
            raise ValidationError("A data não pode ser no passado.")
        return departure_date