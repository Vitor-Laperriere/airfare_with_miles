from django.db import models

class Airport(models.Model):
    name = models.CharField(max_length=255)
    iata_code = models.CharField(max_length=3, unique=True, db_index=True)
    state_code = models.CharField(max_length=3)
    country_code = models.CharField(max_length=3)
    country_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} ({self.iata_code})"
