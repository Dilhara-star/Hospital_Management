from django.contrib import admin  # django's back-office site tools
from .models import UserProfile, PatientProfile, StaffProfile  # our own profile models


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    # columns shown on the UserProfile list page
    list_display = ('get_full_name', 'get_username', 'role', 'get_email', 'phone')
    # filter box on the side of the list page
    list_filter = ('role', 'gender')
    # search box on the list page
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email')

    # shows the linked user's full name as a column
    def get_full_name(self, obj):
        return obj.user.get_full_name()
    get_full_name.short_description = 'Name'

    # shows the linked user's username as a column
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'

    # shows the linked user's email as a column
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'


@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    # columns shown on the PatientProfile list page
    list_display = ('user', 'mrn', 'blood_type', 'status', 'registered_date')
    # filter box on the side of the list page
    list_filter = ('status', 'blood_type')
    # search box on the list page
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'mrn')


@admin.register(StaffProfile)
class StaffProfileAdmin(admin.ModelAdmin):
    # columns shown on the StaffProfile list page
    list_display = ('user', 'employee_id', 'department', 'employment_type')
    # filter box on the side of the list page
    list_filter = ('department', 'employment_type')
    # search box on the list page
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'employee_id')
