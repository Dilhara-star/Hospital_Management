from django.urls import path
from . import views

urlpatterns = [
    path('', views.reports_index, name='reports_index'),
    path('doctor-revenue/', views.doctor_revenue_report, name='doctor_revenue_report'),
    path('appointment-summary/', views.appointment_summary_report, name='appointment_summary_report'),
]
