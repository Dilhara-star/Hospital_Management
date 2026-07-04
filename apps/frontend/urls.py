from django.urls import path
from . import views
from django.conf import settings 
from django.conf.urls.static import static 

urlpatterns = [
    # Home page
    path('', views.frontend_index, name='frontend_index'),
    path('profile/', views.profile_view, name='profile'),
    path('patient-portal/', views.patient_portal, name='patient_portal'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)