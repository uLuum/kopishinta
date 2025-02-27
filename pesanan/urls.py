from django.urls import path
from . import views  # Impor views dari app pesanan
from .views import checkout_view, delete_order, get_orders, update_order_status

urlpatterns = [
    path('', views.pesanan, name='pesanan'),  # URL untuk halaman utama pesanan
    path('tambah_order/', views.tambah_order, name='tambah_order'),  # URL untuk tambah_order   
    path('checkout/<str:order_number>/', views.checkout_view, name='checkout'),
    path('checkout/', checkout_view, name='checkout'),
    path('checkout_summary/', views.checkout_summary, name='checkout_summary'),
    path('pesanan/mark-as-paid/', views.mark_as_paid, name='mark_as_paid'),
    path('delete_order/', delete_order, name='delete_order'),
    path('update-payment-method/', views.update_payment_method, name='update_payment_method'),
    path("orders/", get_orders, name="get_orders"),
    path("update_order/", update_order_status, name="update_order_status"),
]