from .api_client import FlightAPIClient

class FlightService:
    def __init__(self):
        self.client = FlightAPIClient()

    def get_flights(self, origin, destination, departure_date):
        data = self.client.search_flights(origin, destination, departure_date)
        
        flights = []
        for segment in data.get('requestedFlightSegmentList', []):
            for flight in segment.get('flightList', []):
                flight_info = {
                    'airline': flight.get('airline', {}).get('name'),
                    'duration': flight.get('duration', {}).get('hours'),
                    'duration_minutes': flight.get('duration', {}).get('minutes'),
                    'baseMiles': flight.get('fareList', [])[0].get('baseMiles'),
                    'departure_time': flight.get('departure', {}).get('date'),
                    'arrival_time': flight.get('arrival', {}).get('date'),
                }
                flights.append(flight_info)
        return flights
