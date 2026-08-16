# register supplier model so it shows up in the django admin site
from django.contrib import admin  # import django's admin tools
from .models import Supplier  # import our model


# admin settings for the supplier model
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'email', 'status')  # columns shown in the admin list
    list_filter = ('status',)  # filter suppliers by status
    search_fields = ('name', 'contact_person', 'phone', 'email')  # fields you can search by
