from django.db import models

class Status(models.Model):

    name = models.CharField(max_length=50, unique=True, verbose_name="Status Name")
    is_active = models.BooleanField(default=True, verbose_name="Is Active?")

    class Meta:
        verbose_name = "Status"
        verbose_name_plural = "Statuses"

    def __str__(self):
        return self.name


class Country(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Country Name")
    iso_code = models.CharField(max_length=10, unique=True, verbose_name="ISO Code (e.g., JP, CL)")
    #is_active = models.BooleanField(default=True, verbose_name="Is Active?")

    class Meta:
        verbose_name = "Country"
        verbose_name_plural = "Countries"

    def __str__(self):
        return f"{self.name} ({self.iso_code})"


class Currency(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Currency Name")
    iso_code = models.CharField(max_length=10, unique=True, verbose_name="ISO Code (e.g., JPY, USD)")
    symbol = models.CharField(max_length=5, blank=True, verbose_name="Symbol (e.g., $, ¥)")
    #is_active = models.BooleanField(default=True, verbose_name="Is Active?")

    class Meta:
        verbose_name = "Currency"
        verbose_name_plural = "Currencies"

    def __str__(self):
        return f"{self.name} ({self.iso_code})"    