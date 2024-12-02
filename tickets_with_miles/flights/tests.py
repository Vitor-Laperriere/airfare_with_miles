from unittest import TestCase
from datetime import date
from flights.services import FlightService

class FlightServiceSimpleFunctionTest(TestCase):
    def test_generate_smiles_url(self):
        """
        Test the generate_smiles_url function.
        """
        service = FlightService()
        origin = "GIG"
        destination = "MIL"
        departure_date = date(2025, 3, 26)

        url = service.generate_smiles_url(origin, destination, departure_date)

        self.assertIn("originAirport=GIG", url)
        self.assertIn("destinationAirport=MIL", url)
        self.assertIn("departureDate=1743001200000", url)