from datetime import datetime, date, time, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urlencode
import asyncio

from .api_client import FlightAPIClient


class FlightService:
    SMILES_URL_BASE = "https://www.smiles.com.br/mfe/emissao-passagem/"
    SMILES_FARE_TYPES = {'SMILES', 'SMILES_CLUB'}
    DEFAULT_CABIN = 'ALL'
    DEFAULT_ADULTS = 1
    DEFAULT_CHILDREN = 0
    DEFAULT_INFANTS = 0
    DEFAULT_SEARCH_TYPE = 'g3'
    DEFAULT_SEGMENTS = 1
    DEFAULT_TRIP_TYPE = 2
    DEFAULT_DEPARTURE_TIME_HOUR = 15  # 3:00 PM

    def __init__(self, client: Optional[FlightAPIClient] = None):
        """
        Initialize the FlightService with a FlightAPIClient instance.
        """
        self.client = client or FlightAPIClient()

    def get_flights(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        flexibility: int,
    ) -> List[Dict[str, Any]]:
        """
        Fetches and processes flight data for the given parameters using synchronous calls.

        Args:
            origin: The IATA code of the origin airport.
            destination: The IATA code of the destination airport.
            departure_date: The date of departure.
            flexibility: Number of days with forward flexibility.

        Returns:
            A list of dictionaries containing flight information.
        """
        # Run the asynchronous get_flights_internal in an event loop
        return asyncio.run(
            self.get_flights_internal(origin, destination, departure_date, flexibility)
        )

    async def get_flights_internal(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        flexibility: int,
    ) -> List[Dict[str, Any]]:
        """
        Asynchronous internal method to fetch and process flight data.

        Args:
            origin: The IATA code of the origin airport.
            destination: The IATA code of the destination airport.
            departure_date: The date of departure.
            flexibility: Number of days with forward flexibility.

        Returns:
            A list of dictionaries containing flight information.
        """
        flexibility = max(flexibility, 1)
        searches = []
        for delta_days in range(flexibility):
            search_date = departure_date + timedelta(days=delta_days)
            searches.append({
                'origin': origin,
                'destination': destination,
                'departure_date': search_date,
                'adults': self.DEFAULT_ADULTS,
                'children': self.DEFAULT_CHILDREN,
                'infants': self.DEFAULT_INFANTS,
            })

        raw_data_list = await self.client.search_flights_bulk(searches)

        flights = []
        for search_params, raw_data in zip(searches, raw_data_list):
            smiles_url = self.generate_smiles_url(
                search_params['origin'],
                search_params['destination'],
                search_params['departure_date']
            )
            extracted_flights = self.extract_flights(raw_data, smiles_url)
            flights.extend(extracted_flights)

        sorted_flights_list = sorted(flights, key=lambda x: x['miles_cost'])
        return sorted_flights_list

    def generate_smiles_url(
        self,
        origin: str,
        destination: str,
        departure_date: date
    ) -> str:
        """
        Constructs the Smiles URL with the given parameters.

        Args:
            origin: The IATA code of the origin airport.
            destination: The IATA code of the destination airport.
            departure_date: The date of departure.

        Returns:
            A URL string for the Smiles booking page.
        """
        params = {
            'cabin': self.DEFAULT_CABIN,
            'adults': self.DEFAULT_ADULTS,
            'children': self.DEFAULT_CHILDREN,
            'infants': self.DEFAULT_INFANTS,
            'searchType': self.DEFAULT_SEARCH_TYPE,
            'segments': self.DEFAULT_SEGMENTS,
            'tripType': self.DEFAULT_TRIP_TYPE,
            'originAirport': origin,
            'destinationAirport': destination,
            'departureDate': self.date_to_timestamp(departure_date),
        }
        return f"{self.SMILES_URL_BASE}?{urlencode(params)}"

    def date_to_timestamp(self, input_date: date) -> int:
        """
        Converts a date object to a UNIX timestamp in milliseconds at a specific time.

        Args:
            input_date: The date to convert.

        Returns:
            An integer representing the UNIX timestamp in milliseconds.
        """
        combined_datetime = datetime.combine(
            input_date,
            time(self.DEFAULT_DEPARTURE_TIME_HOUR, 0)
        )
        return int(combined_datetime.timestamp() * 1000)

    def extract_flights(
        self,
        raw_data: Dict[str, Any],
        smiles_url: str
    ) -> List[Dict[str, Any]]:
        """
        Extracts flight information from raw API data.

        Args:
            raw_data: The raw data returned from the API client.
            smiles_url: The Smiles booking URL.

        Returns:
            A list of dictionaries containing parsed flight information.
        """
        segments = raw_data.get('requestedFlightSegmentList', [])
        flights = []
        for segment in segments:
            flight_list = segment.get('flightList', [])
            flights.extend(self.parse_flights(flight_list, smiles_url))
        return flights

    def parse_flights(
        self,
        flight_list: List[Dict[str, Any]],
        smiles_url: str
    ) -> List[Dict[str, Any]]:
        """
        Parses a list of flights and extracts relevant information.

        Args:
            flight_list: A list of flight dictionaries from the API.
            smiles_url: The Smiles booking URL.

        Returns:
            A list of dictionaries with cleaned and structured flight data.
        """
        parsed_flights = []
        for flight in flight_list:
            parsed_flight = self.parse_single_flight(flight, smiles_url)
            if parsed_flight and parsed_flight['miles_cost'] != -1:
                parsed_flights.append(parsed_flight)
        return parsed_flights

    def parse_single_flight(
        self,
        flight: Dict[str, Any],
        smiles_url: str
    ) -> Optional[Dict[str, Any]]:
        """
        Parses a single flight and extracts relevant information.

        Args:
            flight: A flight dictionary from the API.
            smiles_url: The Smiles booking URL.

        Returns:
            A dictionary with flight information, or None if parsing fails.
        """
        try:
            departure_time = self.parse_iso_datetime(flight.get('departure', {}).get('date'))
            arrival_time = self.parse_iso_datetime(flight.get('arrival', {}).get('date'))

            return {
                'airline': self.get_airline(flight),
                'miles_cost': self.get_miles_cost(flight),
                'duration_hours': self.get_duration_hours(flight),
                'duration_minutes': self.get_duration_minutes(flight),
                'departure_time': departure_time.isoformat() if departure_time else None,
                'departure_airport': self.get_departure_airport(flight),
                'number_of_stops': self.get_number_of_stops(flight),
                'arrival_time': arrival_time.isoformat() if arrival_time else None,
                'arrival_airport': self.get_arrival_airport(flight),
                'smiles_url': smiles_url,
            }
        except (KeyError, IndexError, TypeError, ValueError):
            # Handle parsing errors gracefully
            return None

    @staticmethod
    def parse_iso_datetime(date_str: Optional[str]) -> Optional[datetime]:
        """
        Parses an ISO formatted date string into a datetime object.

        Args:
            date_str: The ISO formatted date string.

        Returns:
            A datetime object, or None if parsing fails.
        """
        if date_str:
            try:
                return datetime.fromisoformat(date_str)
            except ValueError:
                return None
        return None

    # Attribute Extraction Methods
    def get_airline(self, flight: Dict[str, Any]) -> Optional[str]:
        return flight.get('airline', {}).get('name')

    def get_miles_cost(self, flight: Dict[str, Any]) -> int:
        miles_prices = [
            fare.get('miles', 0)
            for fare in flight.get('fareList', [])
            if fare.get('type') in self.SMILES_FARE_TYPES and fare.get('miles', 0) > 0
        ]
        return min(miles_prices, default=-1)

    def get_duration_hours(self, flight: Dict[str, Any]) -> Optional[int]:
        return flight.get('duration', {}).get('hours')

    def get_duration_minutes(self, flight: Dict[str, Any]) -> Optional[int]:
        return flight.get('duration', {}).get('minutes')

    def get_departure_airport(self, flight: Dict[str, Any]) -> Optional[str]:
        return flight.get('departure', {}).get('airport', {}).get('code')

    def get_number_of_stops(self, flight: Dict[str, Any]) -> int:
        return flight.get('stops', 0)

    def get_arrival_airport(self, flight: Dict[str, Any]) -> Optional[str]:
        return flight.get('arrival', {}).get('airport', {}).get('code')