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
    if request.method == 'POST':
        form = FlightSearchForm(request.POST)
        if form.is_valid():
            origin = form.cleaned_data['origin'].upper()
            destination = form.cleaned_data['destination'].upper()
            departure_date = form.cleaned_data['date']

            flight_service = FlightService()

            try:
                flights = flight_service.get_flights(origin, destination, departure_date)
                if not flights:
                    messages.warning(request, 'Nenhum voo encontrado.')
                else:
                    request.session['flights'] = flights
            except Exception as e:
                logger.error(f"Erro ao buscar voos: {e}")
                messages.error(request, 'Ocorreu um erro ao pesquisar pelos voos.')

            return redirect(reverse('search_flights'))
        else:
            messages.error(request, 'Corrija os erros abaixo.')
    else:
        form = FlightSearchForm()
        flights = request.session.pop('flights', [])

    context = {
        'form': form,
        'flights': flights,
    }
    return render(request, 'flights/search.html', context)