from django.urls import path
from . import views
from django.conf import settings 
from django.conf.urls.static import static 

urlpatterns = [
    path('', views.appointment_form, name='appointment_form'),
    path('my/', views.my_appointments, name='my_appointments'),
    path('my/<int:pk>/', views.my_appointments, name='my_appointment_detail'),
    path('index/', views.appointment_index, name='appointment_index'),
    path('add/', views.appointment_add, name='appointment_add'),
    path('view/<int:pk>/', views.appointment_view, name='appointment_view'),
    path('edit/<int:pk>/', views.appointment_edit, name='appointment_edit'),
    path('edit/<int:pk>/pharmacy-search/', views.appointment_pharmacy_search, name='appointment_pharmacy_search'),
    path('edit/<int:pk>/remove-medicine/<int:item_pk>/', views.prescription_item_delete, name='prescription_item_delete'),
    path('delete/<int:pk>/', views.appointment_delete, name='appointment_delete'),
    path('confirm-payment/<int:pk>/', views.confirm_cash_payment, name='confirm_cash_payment'),
    path('fees/', views.fee_index, name='fee_index'),
    path('pharmacy/', views.pharmacy_queue, name='pharmacy_queue'),
    path('pharmacy/<int:pk>/', views.pharmacy_order_detail, name='pharmacy_order_detail'),
    path('my/<int:pk>/pay-medicine/', views.pay_medicine_online, name='pay_medicine_online'),

    # Reports
    path('reports/', views.reports_index, name='reports_index'),
    path('reports/doctor-revenue/', views.doctor_revenue_report, name='doctor_revenue_report'),
    path('reports/doctor-revenue/pdf/', views.doctor_revenue_report_pdf, name='doctor_revenue_report_pdf'),
    path('reports/appointment-summary/', views.appointment_summary_report, name='appointment_summary_report'),
    path('reports/appointment-summary/pdf/', views.appointment_summary_report_pdf, name='appointment_summary_report_pdf'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)