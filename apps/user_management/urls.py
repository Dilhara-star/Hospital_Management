from django.urls import path  # lets us map a url to a view
from . import views  # our views for this app
from django.conf import settings  # project settings (e.g. DEBUG, MEDIA_URL)
from django.conf.urls.static import static  # serves uploaded files while developing

urlpatterns = [
    # Patient management
    path('patients/', views.patient_user_list, name='patient_user_list'),  # /Users/patients/ shows every patient
    path('patients/add/', views.patient_add, name='patient_add'),  # /Users/patients/add/ registers a new patient
    path('patients/<int:patient_id>/edit/', views.patient_edit, name='patient_edit'),  # edits one patient
    path('patients/<int:patient_id>/detail/', views.patient_detail, name='patient_detail'),  # views one patient
    path('patients/<int:patient_id>/delete/', views.patient_delete, name='patient_delete'),  # deletes one patient

    # Staff management
    path('staff/', views.staff_user_list, name='staff_user_list'),  # /Users/staff/ shows every staff member
    path('staff/add/', views.staff_add, name='staff_add'),  # /Users/staff/add/ adds a new staff member
    path('staff/<int:user_id>/edit/', views.staff_edit, name='staff_edit'),  # edits one staff member
    path('staff/<int:user_id>/detail/', views.staff_detail, name='staff_detail'),  # views one staff member
    path('staff/<int:user_id>/delete/', views.staff_delete, name='staff_delete'),  # deletes one staff member

    # Doctor rooms
    path('doctor-rooms/', views.doctor_room_list, name='doctor_room_list'),  # assigns room numbers to doctors
]

if settings.DEBUG:
    # only while developing: let the browser load uploaded files (e.g. profile pictures)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
