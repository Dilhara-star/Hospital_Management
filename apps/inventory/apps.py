# this file tells django about our new inventory app
from django.apps import AppConfig  # import the base class for app config


# config class for the inventory app
class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # use big auto id for new tables
    name = 'apps.inventory'  # the python path to this app
