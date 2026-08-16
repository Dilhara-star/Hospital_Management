from django.urls import path
from . import views

# public contact-us pages, mounted at "contact/"
urlpatterns = [
    path('index/', views.contact_us_index, name='contact_us_index'),
    path('add_contact/', views.add_contact, name='add_contact'),
]

# staff-facing inquiry management pages, mounted at "dashboard/contact/"
dashboard_urlpatterns = [
    path('list/', views.view_inquiries, name='view_inquiries'),
    path('view_inquiry/<int:id>/', views.view_inquiry, name='view_inquiry'),
    path('mark_solved/<int:id>/', views.mark_inquiry_solved, name='mark_inquiry_solved'),
]
