from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.contrib import messages
from django.urls import reverse
from .forms import FlightSearchForm
from .services import FlightService
import logging

logger = logging.getLogger(__name__)

def search_flights(request: HttpRequest) -> HttpResponse:
    """
    Handles flight search requests and renders the search results.

    Args:
        request: The HttpRequest object.

    Returns:
        An HttpResponse object with the rendered template.
    """
    form = FlightSearchForm(request.POST or None)
    flights = request.session.pop('flights', [])

    if request.method == 'POST':
        if form.is_valid():
            origin = form.cleaned_data['origin'].upper()
            destination = form.cleaned_data['destination'].upper()
            departure_date = form.cleaned_data['date']
            flexibility = int(form.cleaned_data['flexibility'])

            flight_service = FlightService()

            try:
                flights = flight_service.get_flights(origin, destination, departure_date, flexibility)
                if not flights:
                    messages.warning(request, 'Nenhum voo encontrado.')
                else:
                    request.session['flights'] = flights
                    return redirect(reverse('search_flights'))
            except Exception as e:
                logger.error(f"Erro ao buscar voos: {e}")
                messages.error(request, 'Ocorreu um erro ao pesquisar pelos voos.')
        else:
            if form.errors:
                logger.warning(f"Form validation failed: {form.errors}")
                unique_messages = set()
                for field, errors in form.errors.items():
                    for error in errors:
                        unique_message = f"{field.capitalize()}: {error}"
                        if unique_message not in unique_messages:
                            unique_messages.add(unique_message)
                            messages.error(request, unique_message)

    context = {
        'form': form,
        'flights': flights,
    }
    return render(request, 'flights/search.html', context)