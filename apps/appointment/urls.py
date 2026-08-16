from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

# patient-facing appointment pages, mounted at the public "Appointment/" prefix
urlpatterns = [
    path('', views.appointment_form, name='appointment_form'),
    path('my/', views.my_appointments, name='my_appointments'),
    path('my/<int:pk>/', views.my_appointments, name='my_appointment_detail'),
    path('payments/', views.payment_history, name='payment_history'),
    path('my/<int:pk>/bill/appointment.pdf', views.download_appointment_bill, name='download_appointment_bill'),
    path('edit_appointment/<int:pk>/', views.edit_appointment, name='edit_appointment'),
    path('cancel/<int:pk>/', views.cancel_appointment, name='cancel_appointment'),
    path('refund/<int:pk>/', views.refund_appointment, name='refund_appointment'),
    # this is a patient self-service action (finishes their own cancel+refund), so it
    # belongs here next to refund_appointment, not under the staff dashboard prefix below
    path('refund/<int:pk>/process/', views.appointment_refund_process_by_patient, name='process_refund'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# staff-facing appointment management pages, mounted at "dashboard/appointments/"
dashboard_urlpatterns = [
    path('index/', views.appointment_index, name='appointment_index'),
    path('add/', views.appointment_add, name='appointment_add'),
    path('view/<int:pk>/', views.appointment_view, name='appointment_view'),
    path('edit/<int:pk>/', views.appointment_edit, name='appointment_edit'),
    path('delete/<int:pk>/', views.appointment_delete, name='appointment_delete'),
    path('confirm-payment/<int:pk>/', views.confirm_cash_payment, name='confirm_cash_payment'),
    path('fees/', views.fee_index, name='fee_index'),
    path('payments/', views.payment_index, name='payment_index'),
    path('payments/<int:pk>/refund/', views.payment_refund, name='payment_refund'),
]
