from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'department', 'doctor', 'date', 'status', 'created_at')
    list_filter = ('department', 'doctor', 'status')
    search_fields = ('patient__username', 'patient__email', 'patient__first_name', 'patient__last_name')
