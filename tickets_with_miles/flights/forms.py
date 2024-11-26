from django import forms
from django.core.exceptions import ValidationError
from datetime import date

class FlightSearchForm(forms.Form):
    origin = forms.CharField(label='Origin Airport Code', max_length=3)
    destination = forms.CharField(label='Destination Airport Code', max_length=3)
    date = forms.DateField(label='Departure Date', widget=forms.SelectDateWidget)

    def clean_date(self):
        departure_date = self.cleaned_data['date']
        if departure_date < date.today():
            raise ValidationError("Departure date cannot be in the past.")
        return departure_date