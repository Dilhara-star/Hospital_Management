from django.contrib import admin

from .models import Appointment, DepartmentFee, Payment, PrescriptionItem, PharmacyOrder


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'patient_name', 'department', 'doctor', 'date', 'time_slot', 'status', 'created_at')
    list_filter = ('department', 'doctor', 'status')
    search_fields = (
        'patient__username', 'patient__email', 'patient__first_name', 'patient__last_name',
        'patient_name', 'patient_nic', 'patient_contact',
    )


@admin.register(DepartmentFee)
class DepartmentFeeAdmin(admin.ModelAdmin):
    list_display = ('department', 'fee')  # show department and its price in the list


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('appointment', 'amount', 'doctor_fee_amount', 'method', 'status', 'transaction_ref', 'paid_at', 'created_at')
    list_filter = ('method', 'status')
    search_fields = ('transaction_ref', 'appointment__patient_name')


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
