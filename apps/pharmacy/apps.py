# this file tells django about our new pharmacy app
from django.apps import AppConfig  # import the base class for app config


# config class for the pharmacy app
class PharmacyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'  # use big auto id for new tables
    name = 'apps.pharmacy'  # the python path to this app
