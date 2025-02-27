from django.urls import path
from . import views
from .views import menu_view

urlpatterns = [
    path('', menu_view, name='menu'),
    path('edit_menu/<int:menu_id>/', views.edit_menu, name='edit_menu'),  # URL untuk edit_menu
    path('menu/delete/<int:menu_id>/', views.delete_menu, name='delete_menu'),  # URL untuk delete_menu
    path('menu/tambah/', views.tambah_menu, name='tambah_menu'),
]