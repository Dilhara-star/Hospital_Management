from django.urls import path
from . import views
from django.conf import settings 
from django.conf.urls.static import static 

urlpatterns = [
    path('', views.appointment_form, name='appointment_form'),
    path('index/', views.appointment_index, name='appointment_index'),
    path('view/<int:pk>/', views.appointment_view, name='appointment_view'),
    path('delete/<int:pk>/', views.appointment_delete, name='appointment_delete'),
 
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)