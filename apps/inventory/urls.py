# urls for supplier and medicine inventory management
from django.urls import path  # import path to define url routes
from . import views  # import our views

urlpatterns = [
    # Supplier management
    path('suppliers/', views.supplier_list, name='supplier_list'),  # list all suppliers
    path('suppliers/add/', views.supplier_add, name='supplier_add'),  # add a new supplier
    path('suppliers/<int:pk>/edit/', views.supplier_edit, name='supplier_edit'),  # edit a supplier
    path('suppliers/<int:pk>/detail/', views.supplier_detail, name='supplier_detail'),  # view a supplier
    path('suppliers/<int:pk>/delete/', views.supplier_delete, name='supplier_delete'),  # delete a supplier

    # Medicine management
    path('medicines/', views.medicine_list, name='medicine_list'),  # list all medicines
    path('medicines/add/', views.medicine_add, name='medicine_add'),  # add a new medicine
    path('medicines/<int:pk>/edit/', views.medicine_edit, name='medicine_edit'),  # edit a medicine
    path('medicines/<int:pk>/detail/', views.medicine_detail, name='medicine_detail'),  # view a medicine
    path('medicines/<int:pk>/delete/', views.medicine_delete, name='medicine_delete'),  # delete a medicine

    # Stock management
    path('stock/', views.stock_list, name='stock_list'),  # list all stock batches
    path('stock/add/', views.stock_add, name='stock_add'),  # add a new stock batch
    path('stock/<int:pk>/edit/', views.stock_edit, name='stock_edit'),  # edit a stock batch
    path('stock/<int:pk>/detail/', views.stock_detail, name='stock_detail'),  # view a stock batch
    path('stock/<int:pk>/delete/', views.stock_delete, name='stock_delete'),  # delete a stock batch
]
