from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from laporan.views import api_billing_data as laporan_api_billing_data, laporan_keuangan, laporan_inventory_api
from menu.models import MenuItem
from pesanan.models import Pesanan as Pesanan
from laporan.models import Pesanan as LaporanKeuangan
from datetime import datetime, timedelta
from django.utils.timezone import make_aware, localtime, now
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDate
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.views.decorators.csrf import csrf_exempt
import pytz
import logging
import requests
import json

logger = logging.getLogger(__name__)

# Halaman Login
def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')  # Arahkan ke halaman dashboard
        else:
            messages.error(request, 'Username atau password salah.')

    return render(request, 'dashboard/login.html')

def logout_page(request):
    logout(request)
    return redirect('login')

# Halaman Dashboard (Hanya untuk User yang Login)
@login_required
def dashboard_page(request):
    return render(request, 'dashboard/dashboard.html')

# Fungsi untuk mendapatkan data billing di app dashboard
def api_billing_data(request):
    return laporan_keuangan(request)  # Panggil API dari app laporan

def api_inventory_data(request):
    return laporan_inventory_api(request)  # Panggil API dari app laporan

# Fungsi untuk mendapatkan data Best Seller dan Sold Out
def api_best_seller_and_sold_out(request):
    try:
        # Ambil data Best Seller: stok terjual (descending)
        best_seller = (
            MenuItem.objects.all()
            .order_by('-stok_terjual')[:5]  # Ambil 5 item stok terjual terbanyak
            .values('sku', 'nama_item', 'stok_terjual')
        )

        # Ambil data Sold Out: stok saat ini (ascending)
        sold_out = (
            MenuItem.objects.filter(stok_saat_ini__lte=5)  # Contoh filter stok <= 5
            .order_by('stok_saat_ini')[:5]  # Ambil 5 item stok tersisa paling kecil
            .values('sku', 'nama_item', 'stok_saat_ini')
        )

        # Format data untuk dikirim ke frontend
        return JsonResponse({
            'best_seller': list(best_seller),
            'sold_out': list(sold_out),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def api_daily_income_data(request):
    try:
        # Ambil rentang waktu 7 hari terakhir
        today = datetime.now().date()
        past_week = today - timedelta(days=6)

        # Hitung pendapatan per hari
        daily_income = (
            Pesanan.objects.filter(tanggal__date__gte=past_week)
            .annotate(day=F('tanggal__date'))
            .values('day')
            .annotate(total=Sum('total_harga'))
            .order_by('day')
        )

        # Format data untuk frontend
        labels = [str(entry['day']) for entry in daily_income]
        income = [entry['total'] or 0 for entry in daily_income]

        return JsonResponse({'labels': labels, 'income': income})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def api_login(request):
    print(f"Request Method: {request.method}")
    print(f"Raw Body: {request.body}")  # Debugging
    print(f"Headers: {request.headers}")  # Debugging

    if request.method == 'POST':
        try:
            if not request.body:
                return JsonResponse({"success": False, "message": "Body request kosong"}, status=400)

            data = json.loads(request.body)
            print(f"Parsed Data: {data}")

            username = data.get('username')
            password = data.get('password')

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse({"success": True, "message": "Login berhasil"}, status=200)
            else:
                return JsonResponse({"success": False, "message": "Username atau password salah"}, status=400)

        except json.JSONDecodeError:
            return JsonResponse({"success": False, "message": "Format JSON tidak valid"}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)}, status=500)

    return JsonResponse({"success": False, "message": "Metode request tidak valid"}, status=405)

@login_required
def api_order_summary(request):
    summary = (
    Pesanan.objects.aggregate(
        on_order=Count('idorder', filter=Q(status_pesanan__in=['-', 'Belum Bayar'])),
        pesanan_baru=Count('idorder', filter=Q(status_pesanan='Baru')),
        pesanan_diproses=Count('idorder', filter=Q(status_pesanan='Diproses')),
        pesanan_selesai=Count('idorder', filter=Q(status_pesanan='Disajikan'))
        )
    )

    return JsonResponse(summary)
