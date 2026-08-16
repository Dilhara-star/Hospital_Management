from django.contrib import admin

from .models import PrescriptionItem, PharmacyOrder


@admin.register(PrescriptionItem)
class PrescriptionItemAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'medicine', 'dosage', 'quantity', 'created_at')  # columns shown in the list page
    list_filter = ('medicine__category',)  # lets staff filter by medicine category
    search_fields = ('medicine__name', 'appointment__patient_name')  # lets staff search by medicine or patient name


@admin.register(PharmacyOrder)
class PharmacyOrderAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'status', 'total_amount', 'payment_method', 'payment_status', 'dispensed_by', 'completed_at')
    list_filter = ('status', 'payment_method', 'payment_status')
    search_fields = ('appointment__patient_name', 'transaction_ref')
