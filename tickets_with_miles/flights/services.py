from .api_client import FlightAPIClient
from urllib.parse import urlencode


class FlightService:
    def __init__(self):
        self.client = FlightAPIClient()

    def get_flights(self, origin, destination, departure_date):
        """
        Main method to get flights. Orchestrates the flow of fetching, parsing, and returning flight data.
        """
        raw_data = self.fetch_flight_data(origin, destination, departure_date)
        smiles_url = self.generate_smiles_url(origin, destination, departure_date)
        return self.extract_flights(raw_data, smiles_url)

    def fetch_flight_data(self, origin, destination, departure_date):
        """
        Fetches raw flight data from the API client.
        """
        return self.client.search_flights(origin, destination, departure_date)

    def generate_smiles_url(self, origin, destination, departure_date):
        """
        Constructs the Smiles URL with the given parameters.
        """
        params = {
            'cabin': 'ALL',
            'adults': 1,
            'children': 0,
            'infants': 0,
            'originAirport': origin,
            'destinationAirport': destination,
            'departureDate': departure_date
        }
        base_url = "https://www.smiles.com.br/mfe/emissao-passagem/"
        return f"{base_url}?{urlencode(params)}"

    def extract_flights(self, raw_data, smiles_url):
        """
        Extracts a list of flight dictionaries from raw API data.
        """
        segments = raw_data.get('requestedFlightSegmentList', [])
        flights = []
        for segment in segments:
            flight_list = segment.get('flightList', [])
            flights.extend(self.parse_flights(flight_list, smiles_url))
        return flights

    def parse_flights(self, flight_list, smiles_url):
        """
        Parses individual flights from a list and returns a list of dictionaries with cleaned data.
        """
        parsed_flights = []
        for flight in flight_list:
            parsed_flight = self.parse_single_flight(flight, smiles_url)
            if parsed_flight:
                parsed_flights.append(parsed_flight)
        return parsed_flights

    def parse_single_flight(self, flight, smiles_url):
        """
        Parses a single flight dictionary and extracts relevant information.
        """
        try:
            return {
                'airline': self.get_airline(flight),
                'miles_cost': self.get_miles_cost(flight),
                'duration': self.get_duration(flight),
                'duration_minutes': self.get_duration_minutes(flight),
                'departure_time': self.get_departure_time(flight),
                'departure_airport': self.get_departure_airport(flight),
                'number_stops': self.get_number_of_stops(flight),
                'arrival_time': self.get_arrival_time(flight),
                'arrival_airport': self.get_arrival_airport(flight),
                'smiles_url': smiles_url,
            }
        except (KeyError, IndexError, TypeError):
            return None

    # Attribute Extraction Methods
    def get_airline(self, flight):
        return flight.get('airline', {}).get('name')

    def get_miles_cost(self, flight):
        return flight.get('fareList', [{}])[0].get('baseMiles')

    def get_duration(self, flight):
        return flight.get('duration', {}).get('hours')

    def get_duration_minutes(self, flight):
        return flight.get('duration', {}).get('minutes')

    def get_departure_time(self, flight):
        return flight.get('departure', {}).get('date')

    def get_departure_airport(self, flight):
        return flight.get('departure', {}).get('airport', {}).get('code')

    def get_number_of_stops(self, flight):
        return len(flight.get('fareList', [])) - 1

    def get_arrival_time(self, flight):
        return flight.get('arrival', {}).get('date')

    def get_arrival_airport(self, flight):
        return flight.get('arrival', {}).get('airport', {}).get('code')