from django.contrib import admin  # django's admin tools
from .models import Contact_us  # our model

# show the Contact_us model in the django admin site
admin.site.register(Contact_us)
