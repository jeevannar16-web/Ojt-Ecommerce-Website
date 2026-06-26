"""Django app config for the store — registers signals and sets up the application namespace."""

from django.apps import AppConfig


class StoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'store'
