"""
URL configuration for Hospital_Management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.appointment import urls as appointment_urls  # split into patient-facing and staff-facing url lists
from apps.contact import urls as contact_urls  # split into patient-facing and staff-facing url lists
from apps.pharmacy import urls as pharmacy_urls  # split into patient-facing and staff-facing url lists

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('dashboard/', include('apps.dashboard.urls')),
    path('', include('apps.frontend.urls')),
    path('Appointment/', include(appointment_urls.urlpatterns)),  # patient-facing appointment pages
    path('pharmacy/', include(pharmacy_urls.urlpatterns)),  # patient-facing pharmacy pages (pay/download bill)
    path('core/', include('apps.core.urls')),
    path('contact/', include(contact_urls.urlpatterns)),  # public contact-us pages

    # every staff/dashboard page lives under the "dashboard/" prefix
    path('dashboard/users/', include('apps.user_management.urls')),
    path('dashboard/supplier/', include('apps.supplier.urls')),
    path('dashboard/stock/', include('apps.stock.urls')),
    path('dashboard/reports/', include('apps.reports.urls')),
    path('dashboard/appointments/', include(appointment_urls.dashboard_urlpatterns)),  # staff-facing appointment pages
    path('dashboard/pharmacy/', include(pharmacy_urls.dashboard_urlpatterns)),  # staff-facing pharmacy counter pages
    path('dashboard/contact/', include(contact_urls.dashboard_urlpatterns)),  # staff-facing inquiry pages

]


# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
