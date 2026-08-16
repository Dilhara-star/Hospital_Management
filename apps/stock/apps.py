# this file tells django about our new stock app
from django.apps import AppConfig  # import the base class for app config


# config class for the stock app
class StockConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # use big auto id for new tables
    name = 'apps.stock'  # the python path to this app
