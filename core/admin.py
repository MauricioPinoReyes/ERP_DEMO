from django.contrib import admin
from .models import Status, Country, Currency

@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'iso_code')
    search_fields = ('name', 'iso_code')

@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'iso_code', 'symbol')
    search_fields = ('name', 'iso_code')