from django.test import TestCase
from .services import FlightService
from unittest.mock import patch
from datetime import datetime

class FlightServiceTestCase(TestCase):
    @patch('flights.services.FlightAPIClient.search_flights')
    def test_get_flights(self, mock_search_flights):
        mock_response = {
            "requestedFlightSegmentList": [
                {
                    "flightList": [
                        {
                            "airline": {"name": "TAP"},
                            "duration": {"hours": 14, "minutes": 25},
                            "fareList": [{'baseMiles': 215000}],
                            "departure": {"date": "2025-03-26T16:40:00"},
                            "arrival": {"date": "2025-03-27T11:05:00"}
                        }
                    ]
                }
            ]
        }
        mock_search_flights.return_value = mock_response

        flight_service = FlightService()
        flights = flight_service.get_flights('GIG', 'MIL', datetime(2025, 3, 26))

        self.assertEqual(len(flights), 1)
        self.assertEqual(flights[0]['airline'], 'TAP')
        self.assertEqual(flights[0]['duration'], 14)
        self.assertEqual(flights[0]['duration_minutes'], 25)
        self.assertEqual(flights[0]['baseMiles'], 215000)