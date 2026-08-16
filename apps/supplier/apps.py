# this file tells django about our new supplier app
from django.apps import AppConfig  # import the base class for app config


# config class for the supplier app
class SupplierConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # use big auto id for new tables
    name = 'apps.supplier'  # the python path to this app
