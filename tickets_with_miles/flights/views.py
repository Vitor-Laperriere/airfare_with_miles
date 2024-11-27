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
                    error_message = 'Nenhum voo encontrado.'
            except Exception as e:
                logger.error(f"Erro ao buscar voos: {e}")
                error_message = 'Ocorreu um erro ao pesquisar pelos voos.'
        else:
            error_message = 'Corrija os erros abaixo.'
    else:
        form = FlightSearchForm()

    context = {
        'form': form,
        'flights': flights,
        'error_message': error_message,
    }
    return render(request, 'flights/search.html', context)