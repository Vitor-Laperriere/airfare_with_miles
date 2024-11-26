import requests
from django.conf import settings
from datetime import datetime

class FlightAPIClient:
    BASE_URL = 'https://api-air-flightsearch-blue.smiles.com.br/v1/airlines/search'

    def __init__(self):
        self.headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'akamai-bm-telemetry': settings.AKAMAI_TELEMETRY,
            'channel': 'WEB',
            'origin': 'https://www.smiles.com.br',
            'priority': 'u=1, i',
            'referer': 'https://www.smiles.com.br/',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
            'x-api-key': settings.FLIGHT_API_KEY,
        }

    def search_flights(self, origin, destination, departure_date, return_date=None):
        params = {
            'cabin': 'ALL',
            'originAirportCode': origin,
            'destinationAirportCode': destination,
            'departureDate': departure_date.strftime('%Y-%m-%d'),
            'memberNumber': '',
            'adults': 1,
            'children': 0,
            'infants': 0,
            'forceCongener': 'false',
            'cookies': '_gid%3Dundefined%3B'
        }
        if return_date:
            params['returnDate'] = return_date.strftime('%Y-%m-%d')

        response = requests.get(
            self.BASE_URL,
            headers=self.headers,
            params=params,
            timeout=30
        )
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print(f"Response content: {response.content}")
            raise e
        data = response.json()
        return data