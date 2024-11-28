from django import forms
from django.core.exceptions import ValidationError
from datetime import datetime, date
import re


class FlightSearchForm(forms.Form):
    """
    A form to validate and process flight search inputs.
    """
    ORIGIN_PLACEHOLDER = 'Ex.: CNF'
    DESTINATION_PLACEHOLDER = 'Ex.: GRU'
    DATE_INPUT_FORMATS = ['%Y-%m-%d', '%d/%m/%Y']
    AIRPORT_CODE_REGEX = r'^[A-Z]{3}$'
    ERROR_MESSAGES = {
        'origin': "O código da origem deve conter exatamente 3 letras (ex.: CNF).",
        'destination': "O código do destino deve conter exatamente 3 letras (ex.: GRU).",
        'date_past': "A data não pode ser no passado.",
    }

    origin = forms.CharField(
        label='Origem',
        max_length=3,
        min_length=3,
        widget=forms.TextInput(attrs={'placeholder': ORIGIN_PLACEHOLDER}),
    )
    destination = forms.CharField(
        label='Destino',
        max_length=3,
        min_length=3,
        widget=forms.TextInput(attrs={'placeholder': DESTINATION_PLACEHOLDER}),
    )
    date = forms.DateField(
        label='Data',
        widget=forms.DateInput(attrs={'type': 'date'}),
        input_formats=DATE_INPUT_FORMATS,
    )

    def clean_origin(self) -> str:
        """
        Validates the origin field to ensure it is a valid IATA airport code.
        Returns the cleaned origin code in uppercase.
        """
        origin = self.cleaned_data['origin'].upper()
        if not re.match(self.AIRPORT_CODE_REGEX, origin):
            raise ValidationError(self.ERROR_MESSAGES['origin'])
        return origin

    def clean_destination(self) -> str:
        """
        Validates the destination field to ensure it is a valid IATA airport code.
        Returns the cleaned destination code in uppercase.
        """
        destination = self.cleaned_data['destination'].upper()
        if not re.match(self.AIRPORT_CODE_REGEX, destination):
            raise ValidationError(self.ERROR_MESSAGES['destination'])
        return destination

    def clean_date(self) -> datetime.date:
        """
        Validates the date field to ensure it is not in the past.
        Returns the cleaned date.
        """
        departure_date = self.cleaned_data['date']
        if departure_date < date.today():
            raise ValidationError(self.ERROR_MESSAGES['date_past'])
        return departure_date