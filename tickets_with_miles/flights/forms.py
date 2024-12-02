from django import forms
from django.core.exceptions import ValidationError
from datetime import datetime, date, timedelta
from .models import Airport

class FlightSearchForm(forms.Form):
    """
    A form to validate and process flight search inputs.
    """
    ORIGIN_PLACEHOLDER = 'Ex.: CNF'
    DESTINATION_PLACEHOLDER = 'Ex.: GRU'
    ALLOWED_FORWARD_SEARCH_DAYS = 329
    DATE_INPUT_FORMATS = ['%Y-%m-%d', '%d/%m/%Y']

    ERROR_MESSAGES = {
        'origin': "O código da origem não é válido.",
        'destination': "O código do destino não é válido.",
        'date_past': "A data não pode ser no passado.",
        'very_future_date': "A data está muito distante."
    }

    FLEXIBILITY_CHOICES = [
        (0, 'Sem flexibilidade'),
        (3, '3 dias'),
        (7, '7 dias'),
        (15, '15 dias'),
        (30, '30 dias'),
    ]

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
    flexibility = forms.ChoiceField(
        label='Flexibilidade',
        choices=FLEXIBILITY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial=0,
    )

    def clean_origin(self) -> str:
        """
        Validates that the origin IATA code exists in the database.
        """
        origin = self.cleaned_data['origin'].upper()
        if not Airport.objects.filter(iata_code=origin).exists():
            raise ValidationError(self.ERROR_MESSAGES['origin'])
        return origin

    def clean_destination(self) -> str:
        """
        Validates that the destination IATA code exists in the database.
        """
        destination = self.cleaned_data['destination'].upper()
        if not Airport.objects.filter(iata_code=destination).exists():
            raise ValidationError(self.ERROR_MESSAGES['destination'])
        return destination

    def clean_date(self) -> datetime.date:
        """
        Validates that the departure date is not in the past nor too distant.
        """
        departure_date = self.cleaned_data['date']
        if departure_date < date.today():
            raise ValidationError(self.ERROR_MESSAGES['date_past'])
        elif departure_date > date.today() + timedelta(days=self.ALLOWED_FORWARD_SEARCH_DAYS):
            raise ValidationError(self.ERROR_MESSAGES['very_future_date'])
        return departure_date