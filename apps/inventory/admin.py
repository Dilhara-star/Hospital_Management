# register inventory models so they show up in the django admin site
from django.contrib import admin  # import django's admin tools
from .models import Supplier, Medicine, MedicineStock  # import our models


# admin settings for the supplier model
@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'email', 'status')  # columns shown in the admin list
    list_filter = ('status',)  # filter suppliers by status
    search_fields = ('name', 'contact_person', 'phone', 'email')  # fields you can search by


# admin settings for the medicine model
@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'unit', 'reorder_level', 'total_quantity')  # columns shown in the admin list
    list_filter = ('category', 'unit')  # filter medicines by category and unit
    search_fields = ('name', 'manufacturer')  # fields you can search by


# admin settings for the medicine stock model
@admin.register(MedicineStock)
class MedicineStockAdmin(admin.ModelAdmin):
    list_display = ('medicine', 'supplier', 'batch_number', 'quantity', 'expiry_date')  # columns shown in the admin list
    list_filter = ('supplier',)  # filter batches by supplier
    search_fields = ('batch_number', 'medicine__name')  # fields you can search by
