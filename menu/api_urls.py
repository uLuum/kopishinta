from django.urls import path
from .views import MenuItemListView, MenuItemDetailView

urlpatterns = [
    path('menu-items/', MenuItemListView.as_view(), name='menu-items'),
    path('menu-items/<int:idmenu>/', MenuItemDetailView.as_view(), name='menu-item-detail'),
]
