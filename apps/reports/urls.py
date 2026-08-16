from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_index, name='reports_index'),
    path('doctor-revenue/', views.doctor_revenue_report, name='doctor_revenue_report'),
    path('appointment-summary/', views.appointment_summary_report, name='appointment_summary_report'),
    path('hospital-revenue/', views.hospital_revenue_report, name='hospital_revenue_report'),
    path('department-performance/', views.department_performance_report, name='department_performance_report'),
    path('doctors-leaderboard/', views.doctors_leaderboard_report, name='doctors_leaderboard_report'),
    path('appointment-status/', views.hospital_appointment_status_report, name='hospital_appointment_status_report'),
]
