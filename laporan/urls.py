from django.urls import path
from . import views
from .views import laporan_keuangan_view, laporan_inventory_view

urlpatterns = [
    path('laporan', views.laporan_page, name='laporan'), # Halaman laporan
    path('keuangan/', views.laporan_keuangan_api, name='laporan_keuangan_api'),
    path('api/laporan/keuangan/', views.laporan_keuangan, name='laporan-keuangan'),
    path('laporan-keuangan/', laporan_keuangan_view, name='laporan_keuangan'),
    path('inventory/', views.laporan_inventory_api, name='laporan_inventory_api'),
    path('api/laporan/inventory/', views.laporan_inventory_api, name='laporan-inventory'),
    path('laporan-inventory/', laporan_inventory_view, name='laporan_inventory'),
    path('api/billing/', views.api_billing_data, name='api_billing'),  # Endpoint API billing
]
