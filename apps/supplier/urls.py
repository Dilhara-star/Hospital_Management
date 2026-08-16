# urls for supplier management, mounted at "dashboard/supplier/"
from django.urls import path  # import path to define url routes
from . import views  # import our views

urlpatterns = [
    path('', views.supplier_list, name='supplier_list'),  # list all suppliers
    path('add/', views.supplier_add, name='supplier_add'),  # add a new supplier
    path('<int:pk>/edit/', views.supplier_edit, name='supplier_edit'),  # edit a supplier
    path('<int:pk>/detail/', views.supplier_detail, name='supplier_detail'),  # view a supplier
    path('<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),  # delete a supplier
]
