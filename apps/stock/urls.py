# urls for medicine catalog and stock batch management, mounted at "dashboard/stock/"
from django.urls import path  # import path to define url routes
from . import views  # import our views

urlpatterns = [
    # Medicine catalog
    path('medicines/', views.medicine_list, name='medicine_list'),  # list all medicines
    path('medicines/add/', views.medicine_add, name='medicine_add'),  # add a new medicine
    path('medicines/<int:pk>/edit/', views.medicine_edit, name='medicine_edit'),  # edit a medicine
    path('medicines/<int:pk>/detail/', views.medicine_detail, name='medicine_detail'),  # view a medicine
    path('medicines/<int:pk>/delete/', views.medicine_delete, name='medicine_delete'),  # delete a medicine

    # Stock batches
    path('batches/', views.stock_list, name='stock_list'),  # list all stock batches
    path('batches/add/', views.stock_add, name='stock_add'),  # add a new stock batch
    path('batches/<int:pk>/edit/', views.stock_edit, name='stock_edit'),  # edit a stock batch
    path('batches/<int:pk>/detail/', views.stock_detail, name='stock_detail'),  # view a stock batch
    path('batches/<int:pk>/delete/', views.stock_delete, name='stock_delete'),  # delete a stock batch
]
