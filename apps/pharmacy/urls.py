from django.urls import path
from . import views

# patient-facing pharmacy pages, mounted at the public "pharmacy/" prefix
urlpatterns = [
    path('my/<int:pk>/pay-medicine/', views.pay_medicine_online, name='pay_medicine_online'),
    path('my/<int:pk>/bill/medicine.pdf', views.download_medicine_bill, name='download_medicine_bill'),
]

# staff-facing pharmacy counter pages, mounted at "dashboard/pharmacy/"
dashboard_urlpatterns = [
    path('queue/', views.pharmacy_queue, name='pharmacy_queue'),
    path('<int:pk>/', views.pharmacy_order_detail, name='pharmacy_order_detail'),
    path('prescribe/<int:pk>/remove-medicine/<int:item_pk>/', views.prescription_item_delete, name='prescription_item_delete'),
]
