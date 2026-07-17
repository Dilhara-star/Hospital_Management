from django.urls import path
from . import views
from django.conf import settings 
from django.conf.urls.static import static 

urlpatterns = [
    path('', views.appointment_form, name='appointment_form'),
    path('index/', views.appointment_index, name='appointment_index'),
    path('add/', views.appointment_add, name='appointment_add'),
    path('view/<int:pk>/', views.appointment_view, name='appointment_view'),
    path('edit/<int:pk>/', views.appointment_edit, name='appointment_edit'),
    path('edit/<int:pk>/remove-medicine/<int:item_pk>/', views.prescription_item_delete, name='prescription_item_delete'),
    path('delete/<int:pk>/', views.appointment_delete, name='appointment_delete'),
    path('confirm-payment/<int:pk>/', views.confirm_cash_payment, name='confirm_cash_payment'),
    path('fees/', views.fee_index, name='fee_index'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)