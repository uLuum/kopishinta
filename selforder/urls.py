from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls')),
    path('menu/', include('menu.urls')),  # Rute untuk aplikasi menu
    path('api/menu/', include('menu.api_urls')),  # Pisahkan API ke file urls khusus
    path('pesanan/', include('pesanan.urls')),  # Hubungkan ke urls.py di app pesanan
    path('laporan/', include('laporan.urls')),  # Hubungkan ke urls.py di app pesanan
    path('api/laporan/', include('laporan.urls')),  # Menautkan URL laporan
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)