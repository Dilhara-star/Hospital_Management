from django.urls import path
from . import views

urlpatterns = [
    path('index/', views.contact_us_index, name='contact_us_index'),
    path('add_contact/', views.add_contact, name='add_contact'),
    # path('delete_category/<int:id>/', views.delete_category, name='delete_category'),
    # path('view_category/<int:id>/', views.view_category, name='view_category'),
    # path('edit_category/<int:id>/', views.edit_category, name='edit_category'),

]
