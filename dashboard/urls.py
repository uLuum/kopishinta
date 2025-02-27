# dashboard/urls.py
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.login_page, name='login'),  # Halaman Login
    path('login/', views.login_page, name='login'),  # Tambahkan URL /login/
    path('dashboard/', views.dashboard_page, name='dashboard'),  # Halaman Dashboard
    path('logout/', views.logout_page, name='logout'),  # Tambahkan logout
    path('api/login/', views.api_login, name='api_login'),  # Tambahkan URL API Login
    path('api/billing/', views.api_billing_data, name='dashboard_api_billing'),  # API untuk billing
    path('api/inventory/', views.api_inventory_data, name='dashboard_api_inventory'),  # API untuk inventory
    path('api/best-seller-sold-out/', views.api_best_seller_and_sold_out, name='dashboard_api_best_seller_sold_out'),
    path('api/daily-income/', views.api_daily_income_data, name='api_daily_income'),
    path('api/order-summary/', views.api_order_summary, name='api_order_summary'),  
]