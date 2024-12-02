import os
import csv
from django.core.management.base import BaseCommand
from flights.models import Airport

class Command(BaseCommand):
    help = 'Loads airports from a CSV file'

    def handle(self, *args, **kwargs):

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        csv_path = os.path.join(base_dir, 'data', 'airports.csv')

        with open(csv_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                Airport.objects.create(
                    name = row['name'],
                    iata_code = row['iata_code'],
                    state_code =row['state_code'],
                    country_code = row['country_code'],
                    country_name = row['country_name'],
                )
        self.stdout.write(self.style.SUCCESS('Airports loaded with success!'))