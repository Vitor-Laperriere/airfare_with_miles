import asyncio
from datetime import date, timedelta
from unittest import TestCase
from unittest.mock import patch, MagicMock
from django.test import TestCase as DjangoTestCase
from django.core.exceptions import ValidationError

from flights.models import Airport
from flights.forms import FlightSearchForm
from flights.services import FlightService
from flights.api_client import FlightAPIClient
from aiohttp import ClientError


class MockAiohttpResponse:
    def __init__(self, json_data=None, raise_exc=None):
        self.json_data = json_data or {}
        self.raise_exc = raise_exc

    async def __aenter__(self):
        if self.raise_exc:
            raise self.raise_exc
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def raise_for_status(self):
        return

    async def json(self):
        return self.json_data



class AirportModelTest(DjangoTestCase):
    def test_create_airport(self):
        a = Airport.objects.create(
            name="Confins",
            iata_code="CNF",
            state_code="MG",
            country_code="BR",
            country_name="Brasil"
        )

        self.assertEqual(a.name, "Confins")

    def test_unique_iata_code(self):
        Airport.objects.create(
            name='Guarulhos',
            iata_code='GRU',
            state_code='SP',
            country_code='BR',
            country_name='Brasil'
        )
        with self.assertRaises(Exception):
            Airport.objects.create(
                name='Outro Aeroporto',
                iata_code='GRU',
                state_code='SP',
                country_code='BR',
                country_name='Brasil'
            )

    def test_str_representation(self):
        a = Airport.objects.create(
            name='Congonhas',
            iata_code='CGH',
            state_code='SP',
            country_code='BR',
            country_name='Brasil'
        )

        self.assertEqual(str(a), "Congonhas (CGH)")

    def test_search_by_iata_code(self):
        Airport.objects.create(
            name='Santos Dumont',
            iata_code='SDU',
            state_code='RJ',
            country_code='BR',
            country_name='Brasil'
        )

        self.assertTrue(Airport.objects.filter(iata_code='SDU').exists())

    def test_db_index_on_iata_code(self):
        field = Airport._meta.get_field('iata_code')

        self.assertTrue(field.db_index)


class FlightSearchFormTest(DjangoTestCase):
    @classmethod
    def setUpTestData(cls):
        Airport.objects.create(
            name='Confins', iata_code='CNF', state_code='MG', country_code='BR', country_name='Brasil'
        )
        Airport.objects.create(
            name='Guarulhos', iata_code='GRU', state_code='SP', country_code='BR', country_name='Brasil'
        )

    def test_valid_form(self):
        form = FlightSearchForm(data={
            'origin': 'CNF',
            'destination': 'GRU',
            'date': (date.today() + timedelta(days=10)).isoformat(),
            'flexibility': 0
        })

        self.assertTrue(form.is_valid())

    def test_invalid_origin(self):
        form = FlightSearchForm(data={
            'origin': 'XXX',
            'destination': 'GRU',
            'date': (date.today() + timedelta(days=1)).isoformat(),
            'flexibility': 0
        })

        self.assertFalse(form.is_valid())
        self.assertIn('origin', form.errors)

    def test_invalid_destination(self):
        form = FlightSearchForm(data={
            'origin': 'CNF',
            'destination': 'XXX',
            'date': (date.today() + timedelta(days=1)).isoformat(),
            'flexibility': 0
        })

        self.assertFalse(form.is_valid())
        self.assertIn('destination', form.errors)

    def test_date_in_past(self):
        form = FlightSearchForm(data={
            'origin': 'CNF',
            'destination': 'GRU',
            'date': (date.today() - timedelta(days=1)).isoformat(),
            'flexibility': 0
        })

        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)

    def test_very_future_date(self):
        form = FlightSearchForm(data={
            'origin': 'CNF',
            'destination': 'GRU',
            'date': (date.today() + timedelta(days=330)).isoformat(),
            'flexibility': 0
        })

        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)

    def test_allowed_future_date(self):
        form = FlightSearchForm(data={
            'origin': 'CNF',
            'destination': 'GRU',
            'date': (date.today() + timedelta(days=100)).isoformat(),
            'flexibility': 0
        })

        self.assertTrue(form.is_valid())


class FlightServiceTest(DjangoTestCase):
    def setUp(self):
        self.service = FlightService()

    def test_generate_smiles_url(self):
        url = self.service.generate_smiles_url('CNF','GRU',date(2025,3,10))

        self.assertIn('originAirport=CNF', url)
        self.assertIn('destinationAirport=GRU', url)
        self.assertIn('departureDate=', url)

    @patch.object(FlightAPIClient, 'search_flights_bulk', return_value=[])
    def test_get_flights_empty_results(self, mock_search):
        flights = self.service.get_flights('CNF','GRU',date.today(),1)

        self.assertEqual(flights, [])

    @patch.object(FlightAPIClient, 'search_flights_bulk')
    def test_get_flights_sorted_by_miles(self, mock_search):
        mock_search.return_value = [
            {'requestedFlightSegmentList': [{'flightList': [
                {'fareList': [{'type': 'SMILES','miles':15000}],
                 'departure':{'date':'2024-12-20T10:00:00'},
                 'arrival':{'date':'2024-12-20T12:00:00'}}
            ]}]},
            {'requestedFlightSegmentList': [{'flightList': [
                {'fareList': [{'type': 'SMILES','miles':10000}],
                 'departure':{'date':'2024-12-21T10:00:00'},
                 'arrival':{'date':'2024-12-21T12:00:00'}}
            ]}]}
        ]
        flights = self.service.get_flights('CNF','GRU',date.today(),2)

        self.assertEqual(len(flights), 2)
        self.assertEqual(flights[0]['miles_cost'], 10000)

    @patch.object(FlightAPIClient, 'search_flights_bulk', return_value=[])
    def test_get_flights_flexibility(self, mock_search):
        self.service.get_flights('CNF','GRU',date.today(),3)
        calls = mock_search.call_args[0][0]

        self.assertEqual(len(calls), 3)

    def test_date_to_timestamp(self):
        ts = self.service.date_to_timestamp(date(2025,3,26))

        self.assertIsInstance(ts,int)

    def test_get_airline(self):
        flight = {'airline':{'name':'GOL'}}

        self.assertEqual(self.service.get_airline(flight),'GOL')

    def test_get_miles_cost_no_valid_fare(self):
        flight = {'fareList':[{'type':'CASH','miles':0}]}

        self.assertEqual(self.service.get_miles_cost(flight), -1)

    def test_get_miles_cost_valid_fare(self):
        flight = {'fareList':[
            {'type':'SMILES_CLUB','miles':20000},
            {'type':'SMILES','miles':15000}
        ]}

        self.assertEqual(self.service.get_miles_cost(flight),15000)

    def test_extract_flights_empty(self):
        raw_data = {}
        flights = self.service.extract_flights(raw_data,"http://ex.com")

        self.assertEqual(flights,[])


class FlightAPIClientTest(TestCase):
    @patch('aiohttp.ClientSession.get')
    def test_search_flights_success(self, mock_get):
        mock_get.return_value = MockAiohttpResponse({"ok":True})
        client = FlightAPIClient(api_key='dummy', telemetry='dummy')
        result = asyncio.run(client.search_flights('CNF','GRU',date.today()))

        self.assertTrue(result.get('ok'))

    @patch('aiohttp.ClientSession.get')
    def test_search_flights_with_return_date(self, mock_get):
        mock_get.return_value = MockAiohttpResponse({"ok":True})
        client = FlightAPIClient(api_key='dummy', telemetry='dummy')
        result = asyncio.run(client.search_flights('CNF','GRU',date.today(), date.today()+timedelta(days=5)))

        self.assertTrue(result.get('ok'))

    @patch('aiohttp.ClientSession.get')
    def test_search_flights_bulk(self, mock_get):
        mock_get.return_value = MockAiohttpResponse({"flight":"data"})
        client = FlightAPIClient(api_key='dummy', telemetry='dummy')
        searches = [
            {'origin':'CNF','destination':'GRU','departure_date':date.today()},
            {'origin':'GRU','destination':'CNF','departure_date':date.today()+timedelta(days=1)}
        ]
        results = asyncio.run(client.search_flights_bulk(searches))

        self.assertEqual(len(results),2)
        self.assertEqual(results[0],{'flight':'data'})

    @patch('aiohttp.ClientSession.get')
    def test_search_flights_bulk_multiple(self, mock_get):
        mock_get.return_value = MockAiohttpResponse({"result":"ok"})
        client = FlightAPIClient(api_key='dummy', telemetry='dummy')
        searches = [
            {'origin':'CNF','destination':'GRU','departure_date':date.today()},
            {'origin':'GRU','destination':'CNF','departure_date':date.today()+timedelta(days=1)},
            {'origin':'GIG','destination':'BSB','departure_date':date.today()+timedelta(days=2)}
        ]
        results = asyncio.run(client.search_flights_bulk(searches))

        self.assertEqual(len(results),3)
        self.assertEqual(results[0],{'result':'ok'})

    @patch('aiohttp.ClientSession.get')
    def test_search_flights_params(self, mock_get):
        mock_get.return_value = MockAiohttpResponse({})
        client = FlightAPIClient(api_key='dummy', telemetry='dummy')
        date_ = date.today()
        asyncio.run(client.search_flights('CNF','GRU',date_))
        called_args = mock_get.call_args[1]['params']

        self.assertEqual(called_args['originAirportCode'],'CNF')
        self.assertEqual(called_args['destinationAirportCode'],'GRU')

    @patch('aiohttp.ClientSession.get')
    def test_search_flights_empty_json(self, mock_get):
        mock_get.return_value = MockAiohttpResponse({})
        client = FlightAPIClient(api_key='dummy', telemetry='dummy')
        result = asyncio.run(client.search_flights('CNF','GRU',date.today()))

        self.assertEqual(result, {})


class AdditionalTests(DjangoTestCase):
    def setUp(self):
        self.service = FlightService()
        Airport.objects.create(
            name='Confins', iata_code='CNF', state_code='MG', country_code='BR', country_name='Brasil'
        )

    def test_parse_flights_no_valid_fares(self):

        flight_list = [
            {
                'fareList': [{'type': 'CASH', 'miles': 0}],
                'departure': {'date': '2025-03-10T10:00:00'},
                'arrival': {'date': '2025-03-10T12:00:00'}
            }
        ]
        result = self.service.parse_flights(flight_list, "http://example.com")

        self.assertEqual(result, [])

    def test_parse_flights_multiple_valid_flights(self):
        flight_list = [
            {
                'fareList': [{'type': 'SMILES', 'miles': 10000}],
                'departure': {'date': '2025-03-10T10:00:00', 'airport': {'code': 'CNF'}},
                'arrival': {'date': '2025-03-10T12:00:00', 'airport': {'code': 'GRU'}}
            },
            {
                'fareList': [{'type': 'SMILES', 'miles': 15000}],
                'departure': {'date': '2025-03-11T08:00:00', 'airport': {'code': 'CNF'}},
                'arrival': {'date': '2025-03-11T10:00:00', 'airport': {'code': 'GRU'}}
            }
        ]
        result = self.service.parse_flights(flight_list, "http://example.com")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['miles_cost'], 10000)
        self.assertEqual(result[1]['miles_cost'], 15000)

    def test_form_missing_destination(self):

        form = FlightSearchForm(data={
            'origin': 'CNF',
            'date': (date.today() + timedelta(days=10)).isoformat(),
            'flexibility': 0
        })

        self.assertFalse(form.is_valid())
        self.assertIn('destination', form.errors)

    @patch('aiohttp.ClientSession.get')
    def test_api_client_invalid_origin_destination(self, mock_get):

        mock_get.return_value = MockAiohttpResponse(raise_exc=ClientError("Invalid Input"))
        client = FlightAPIClient(api_key='dummy', telemetry='dummy')
        result = asyncio.run(client.search_flights('', '', date.today()))
        self.assertIn('error', result)

class EdgeCaseTests(DjangoTestCase):
    @classmethod
    def setUpTestData(cls):

        Airport.objects.create(
            name='Confins', iata_code='CNF', state_code='MG', country_code='BR', country_name='Brasil'
        )
        Airport.objects.create(
            name='Guarulhos', iata_code='GRU', state_code='SP', country_code='BR', country_name='Brasil'
        )
        cls.service = FlightService()


    def test_form_date_is_today(self):
     
        form = FlightSearchForm(data={
            'origin': 'CNF',
            'destination': 'GRU',
            'date': date.today().isoformat(),
            'flexibility': 0
        })
       
        self.assertTrue(form.is_valid(), "A data de hoje deveria ser válida se não é passado")

    def test_form_max_allowed_future_date(self):
      
        max_allowed_date = date.today() + timedelta(days=329)
        form = FlightSearchForm(data={
            'origin': 'CNF',
            'destination': 'GRU',
            'date': max_allowed_date.isoformat(),
            'flexibility': 0
        })

        self.assertTrue(form.is_valid(), "A data máxima permitida deveria ser válida")


    def test_get_flights_zero_flexibility(self):
       
        with patch.object(FlightAPIClient, 'search_flights_bulk', return_value=[]) as mock_search:
            self.service.get_flights('CNF','GRU',date.today(),0)
            calls = mock_search.call_args[0][0]

            self.assertEqual(len(calls), 1, "Com flex=0 deve haver apenas 1 busca")

    def test_extract_flights_empty_flight_list(self):
        
        raw_data = {
            'requestedFlightSegmentList': [
                {'flightList': []}
            ]
        }
        flights = self.service.extract_flights(raw_data, "http://ex.com")

        self.assertEqual(flights, [], "Sem voos em flightList deve retornar lista vazia")


    @patch('aiohttp.ClientSession.get')
    def test_search_flights_many_passengers(self, mock_get):
      
        mock_get.return_value = MockAiohttpResponse({})
        client = FlightAPIClient(api_key='dummy', telemetry='dummy')
        asyncio.run(client.search_flights('CNF','GRU',date.today(), None, adults=10, children=5, infants=3))
        called_args = mock_get.call_args[1]['params']

        self.assertEqual(called_args['adults'], 10)
        self.assertEqual(called_args['children'], 5)
        self.assertEqual(called_args['infants'], 3)

    @patch('aiohttp.ClientSession.get')
    def test_search_flights_bulk_empty_searches(self, mock_get):
       
        mock_get.return_value = MockAiohttpResponse({"flight":"data"})
        client = FlightAPIClient(api_key='dummy', telemetry='dummy')
        results = asyncio.run(client.search_flights_bulk([]))

        self.assertEqual(results, [], "Sem buscas deve retornar lista vazia")

    @patch('aiohttp.ClientSession.get')
    def test_search_flights_numeric_airports(self, mock_get):
      
        mock_get.return_value = MockAiohttpResponse({"ok":True})
        client = FlightAPIClient(api_key='dummy', telemetry='dummy')
        result = asyncio.run(client.search_flights('123','456',date.today()))
    
        self.assertTrue(result.get('ok'), "Códigos numéricos não devem causar erro no client")

