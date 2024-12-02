import aiohttp
import asyncio
from datetime import date
from typing import Optional, Dict, Any, List
from django.conf import settings


class FlightAPIClient:
    """
    Client to interact with the Smiles Flight Search API.
    """

    BASE_URL = 'https://api-air-flightsearch-blue.smiles.com.br/v1/airlines/search'
    TIMEOUT = 30  # seconds

    def __init__(self, api_key: Optional[str] = None, telemetry: Optional[str] = None):
        """
        Initialize the FlightAPIClient with necessary headers.

        Args:
            api_key: The API key for authentication.
            telemetry: Akamai telemetry token.
        """
        self.api_key = api_key or settings.FLIGHT_API_KEY
        self.telemetry = telemetry or settings.AKAMAI_TELEMETRY

        self.headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Akamai-BM-Telemetry': self.telemetry,
            'Channel': 'WEB',
            'Origin': 'https://www.smiles.com.br',
            'Priority': 'u=1, i',
            'Referer': 'https://www.smiles.com.br/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'User-Agent': (
                'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) '
                'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 '
                'Mobile/15E148 Safari/604.1'
            ),
            'x-api-key': self.api_key,
        }

    async def fetch(self, session: aiohttp.ClientSession, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Helper method to fetch data from the API.

        Args:
            session: The aiohttp ClientSession.
            params: The query parameters for the API request.

        Returns:
            A dictionary containing the API response data.
        """
        try:
            async with session.get(
                self.BASE_URL,
                headers=self.headers,
                params=params,
                timeout=self.TIMEOUT
            ) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            return {'error': str(e)}

    async def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        return_date: Optional[date] = None,
        adults: int = 1,
        children: int = 0,
        infants: int = 0,
    ) -> Dict[str, Any]:
        """
        Searches for flights using the Smiles API.

        Args:
            origin: IATA code of the origin airport.
            destination: IATA code of the destination airport.
            departure_date: Date of departure.
            return_date: Date of return, if applicable.
            adults: Number of adult passengers.
            children: Number of child passengers.
            infants: Number of infant passengers.

        Returns:
            A dictionary containing the API response data.

        Raises:
            aiohttp.ClientError: An error occurred while making the API request.
        """
        params = {
            'cabin': 'ALL',
            'originAirportCode': origin,
            'destinationAirportCode': destination,
            'departureDate': departure_date.strftime('%Y-%m-%d'),
            'adults': adults,
            'children': children,
            'infants': infants,
            'forceCongener': 'false',
            'cookies': '_gid%3Dundefined%3B',
            'memberNumber': '',
        }

        if return_date:
            params['returnDate'] = return_date.strftime('%Y-%m-%d')

        async with aiohttp.ClientSession() as session:
            return await self.fetch(session, params)

    async def search_flights_bulk(
        self,
        searches: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Searches for flights using the Smiles API in parallel.

        Args:
            searches: A list of dictionaries containing search parameters. Each dictionary should
                      have keys: 'origin', 'destination', 'departure_date', and optionally
                      'return_date', 'adults', 'children', 'infants'.

        Returns:
            A list of dictionaries containing the API response data for each search.

        Raises:
            aiohttp.ClientError: An error occurred while making the API requests.
        """
        async with aiohttp.ClientSession() as session:
            tasks = []
            for search in searches:
                params = {
                    'cabin': 'ALL',
                    'originAirportCode': search['origin'],
                    'destinationAirportCode': search['destination'],
                    'departureDate': search['departure_date'].strftime('%Y-%m-%d'),
                    'adults': search.get('adults', 1),
                    'children': search.get('children', 0),
                    'infants': search.get('infants', 0),
                    'forceCongener': 'false',
                    'cookies': '_gid%3Dundefined%3B',
                    'memberNumber': '',
                }
                if search.get('return_date'):
                    params['returnDate'] = search['return_date'].strftime('%Y-%m-%d')

                tasks.append(self.fetch(session, params))

            results = await asyncio.gather(*tasks)
            return results
