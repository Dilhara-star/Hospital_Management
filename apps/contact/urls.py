from django.urls import path
from . import views

urlpatterns = [
    #frontend start here
    path('index/', views.contact_us_index, name='contact_us_index'), 
    path('add_contact/', views.add_contact, name='add_contact'),
    # path('delete_category/<int:id>/', views.delete_category, name='delete_category'),


  #dash board start here
    path('list/', views.view_inquiries, name='view_inquiries'),
    path('view_inquiry/<int:id>/', views.view_inquiry, name='view_inquiry'),
    # path('edit_category/<int:id>/', views.edit_category, name='edit_category'),

]
