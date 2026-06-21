from django.urls import path
from . import views
from django.conf import settings 
from django.conf.urls.static import static 

urlpatterns = [
    path('', views.dashboard_index, name='dashboard_index'),
#     path('add/', views.product_add, name='product_add'),
#     path('create/', views.product_create, name='product_create'),
#     path('<int:pk>/edit/', views.product_edit, name='product_edit'),
#     path('<int:pk>/update/', views.product_update, name='product_update'),
#     path('<int:pk>/delete/', views.product_delete, name='product_delete'),
#     path('view/<int:pk>/', views.product_view, name='product_view'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)