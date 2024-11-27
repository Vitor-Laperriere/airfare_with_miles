from django.shortcuts import render, redirect
from .forms import FlightSearchForm
from .services import FlightService
import logging

logger = logging.getLogger(__name__)

def search_flights(request):
    # Inicialize os valores padrão
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

            # Salve os resultados na sessão e redirecione
            request.session['flights'] = flights
            request.session['error_message'] = error_message
            return redirect('search_flights')  # Redirecione para evitar o reenvio do formulário
        else:
            error_message = 'Corrija os erros abaixo.'
    else:
        # Método GET: Inicialize o formulário e recupere dados da sessão (se existirem)
        form = FlightSearchForm()
        flights = request.session.pop('flights', [])
        error_message = request.session.pop('error_message', '')

    # Contexto para renderização do template
    context = {
        'form': form,
        'flights': flights,
        'error_message': error_message,
    }
    return render(request, 'flights/search.html', context)