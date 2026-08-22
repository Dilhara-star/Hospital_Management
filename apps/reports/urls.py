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
    path('low-stock/', views.low_stock_report, name='low_stock_report'),
    path('medicine-expiry/', views.medicine_expiry_report, name='medicine_expiry_report'),
    path('medicine-sales/', views.medicine_sales_report, name='medicine_sales_report'),
    path('stock-valuation/', views.stock_valuation_report, name='stock_valuation_report'),
    path('patient-registration/', views.patient_registration_report, name='patient_registration_report'),
    path('staff-headcount/', views.staff_headcount_report, name='staff_headcount_report'),
    path('patient-history/', views.patient_medical_history_report, name='patient_medical_history_report'),
    path('appointment-revenue-trend/', views.appointment_revenue_trend_report, name='appointment_revenue_trend_report'),
    path('outstanding-payments/', views.outstanding_payments_report, name='outstanding_payments_report'),
    path('current-stock/', views.stock_inventory_report, name='stock_inventory_report'),
    path('doctor-schedule/', views.doctor_schedule_report, name='doctor_schedule_report'),
    path('patient-demographics/', views.patient_demographics_report, name='patient_demographics_report'),
    path('refunds/', views.refund_report, name='refund_report'),
    path('purchase/', views.purchase_report, name='purchase_report'),
]
