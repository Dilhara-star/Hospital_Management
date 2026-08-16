from django.urls import path
from . import views
from django.conf import settings 
from django.conf.urls.static import static 

urlpatterns = [
    path('', views.dashboard_index, name='dashboard_index'),
    path('register/', views.register_view, name='register'),
    path('profile/', views.dashboard_profile, name='dashboard_profile'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)