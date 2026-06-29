from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # General
    path('', views.user_list, name='user_list'),
    path('add/', views.user_create, name='user_add'),
    path('create/', views.user_create, name='user_create'),
    path('<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('<int:user_id>/delete/', views.user_delete, name='user_delete'),

    # Patient management
    path('patients/', views.patient_user_list, name='patient_user_list'),
    path('patients/add/', views.patient_add, name='patient_add'),
    path('patients/<int:patient_id>/edit/', views.patient_edit, name='patient_edit'),
    path('patients/<int:patient_id>/detail/', views.patient_detail, name='patient_detail'),
    path('patients/<int:patient_id>/delete/', views.patient_delete, name='patient_delete'),

    # Staff management
    path('staff/', views.staff_user_list, name='staff_user_list'),
    path('staff/<int:user_id>/edit/', views.staff_edit, name='staff_edit'),
    path('staff/<int:user_id>/detail/', views.staff_detail, name='staff_detail'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
