import requests
from django.shortcuts import render
from .forms import FlightSearchForm
from .services import FlightService
import logging

logger = logging.getLogger(__name__)

def search_flights(request):
    flights = []
    error_message = ''

    if request.method == 'POST':
        form = FlightSearchForm(request.POST)
        if form.is_valid():
            origin = form.cleaned_data['origin'].upper()
            destination = form.cleaned_data['destination'].upper()
            date = form.cleaned_data['date']

            flight_service = FlightService()

            try:
                flights = flight_service.get_flights(origin, destination, date)
                if not flights:
                    error_message = 'No flights found for the selected criteria.'
            except Exception as e:
                logger.error(f"Error fetching flights: {e}")
                error_message = 'An error occurred while fetching flight data.'
        else:
            error_message = 'Please correct the errors below.'
    else:
        form = FlightSearchForm()

    context = {
        'form': form,
        'flights': flights,
        'error_message': error_message,
    }
    return render(request, 'flights/search.html', context)