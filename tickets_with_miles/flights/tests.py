from django.test import TestCase
from unittest.mock import patch
from datetime import date
from flights.services import FlightService

class FlightServiceTestCase(TestCase):

    @patch('flights.services.FlightAPIClient.search_flights')
    def test_get_flights(self, mock_search_flights):
        """
        Test the get_flights method of the FlightService class.
        """
        
        mock_response = {
            "requestedFlightSegmentList": [
                {
                    "flightList": [
                        {
                            "airline": {"name": "TAP"},
                            "duration": {"hours": 14, "minutes": 25},
                            "fareList": [{"miles": 215000, "type": "SMILES"}],
                            "departure": {"date": "2025-03-26T16:40:00"},
                            "arrival": {"date": "2025-03-27T11:05:00"},
                            "stops": 1,
                            "departure": {"airport": {"code": "GIG"}},
                            "arrival": {"airport": {"code": "MIL"}}
                        }
                    ]
                }
            ]
        }
        mock_search_flights.return_value = mock_response

        flight_service = FlightService()
        flights = flight_service.get_flights("GIG", "MIL", date(2025, 3, 26))

        self.assertEqual(len(flights), 1)
        self.assertEqual(flights[0]['airline'], 'TAP')
        self.assertEqual(flights[0]['duration_hours'], 14)
        self.assertEqual(flights[0]['duration_minutes'], 25)
        self.assertEqual(flights[0]['miles_cost'], 215000)
        self.assertEqual(flights[0]['departure_time'], "2025-03-26T16:40:00")
        self.assertEqual(flights[0]['arrival_time'], "2025-03-27T11:05:00")
        self.assertEqual(flights[0]['number_of_stops'], 1)
        self.assertEqual(flights[0]['departure_airport'], "GIG")
        self.assertEqual(flights[0]['arrival_airport'], "MIL")