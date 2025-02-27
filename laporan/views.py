from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from .models import Pesanan, LaporanKeuangan, MenuItem
from pesanan.models import Pesanan, PesananDetail  # Pastikan model ini sesuai dengan yang Anda gunakan
from menu.models import MenuItem  # Model menu
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F, Q, Sum
from django.utils.dateparse import parse_date
from datetime import datetime, timedelta
from django.utils.timezone import localtime, make_aware, now
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import json
import csv
import logging
import pytz

logger = logging.getLogger(__name__)
@login_required
@csrf_exempt

def laporan_page(request):
    return render(request, 'laporan_keuangan.html')

# Laporan Keuangan
def laporan_keuangan(request):
    try:
        # Ambil timezone Asia/Jakarta
        local_tz = pytz.timezone('Asia/Jakarta')
        now = datetime.now(local_tz)

        # Rentang waktu untuk perhitungan
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_yesterday = start_of_today - timedelta(days=1)
        end_of_yesterday = start_of_today - timedelta(microseconds=1)
        start_of_week = start_of_today - timedelta(days=7)
        start_of_month = start_of_today - timedelta(days=30)

        # Hitung pendapatan berdasarkan periode
        total_today = Pesanan.objects.filter(
            tanggal__range=(start_of_today, now)
        ).aggregate(Sum('total_harga'))['total_harga__sum'] or 0

        total_yesterday = Pesanan.objects.filter(
            tanggal__range=(start_of_yesterday, end_of_yesterday)
        ).aggregate(Sum('total_harga'))['total_harga__sum'] or 0

        total_week = Pesanan.objects.filter(
            tanggal__range=(start_of_week, now)
        ).aggregate(Sum('total_harga'))['total_harga__sum'] or 0

        total_month = Pesanan.objects.filter(
            tanggal__range=(start_of_month, now)
        ).aggregate(Sum('total_harga'))['total_harga__sum'] or 0

        # Format data laporan
        laporan_data = [
            {
                'tanggal': localtime(p.tanggal).strftime('%d-%m-%Y %H:%M'),
                'nomor_order': p.nomor_order,
                'layanan': p.layanan,
                'total_harga': f"Rp {int(p.total_harga):,}".replace(",", "."),
                'metode_pembayaran': p.metode_bayar,
                'status_bayar': p.status,
            }
            for p in Pesanan.objects.all()
        ]

        return JsonResponse({
            'laporan': laporan_data,
            'total_today': total_today,
            'total_yesterday': total_yesterday,
            'total_week': total_week,
            'total_month': total_month
        }, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    
def laporan_keuangan_api(request):
    try:
        pesanan_list = Pesanan.objects.all()
        laporan_data = []

        for pesanan_obj in pesanan_list:
            laporan_data.append({
                'tanggal': localtime(pesanan_obj.tanggal).strftime('%d-%m-%Y %H:%M'),  # Format tanggal lokal
                'nomor_order': pesanan_obj.nomor_order,
                'layanan': pesanan_obj.layanan,
                'total_harga': f"Rp {int(pesanan_obj.total_harga):,}".replace(",", "."),  # Format harga
                'metode_pembayaran': pesanan_obj.metode_bayar,  # Gunakan nama properti sesuai frontend
                'status_bayar': pesanan_obj.status,  # Gunakan nama properti sesuai frontend
            })

        return JsonResponse({'laporan': laporan_data}, safe=False)
    except Exception as e:
        logger.error(f"Error fetching financial report data: {e}")
        return JsonResponse({'error': 'Error fetching financial report data'}, status=500)

def laporan_keuangan_view(request):
    laporan = LaporanKeuangan.objects.all()
    return render(request, 'laporan_keuangan.html', {'laporan': laporan})

def get_laporan_keuangan(request):
    laporan = LaporanKeuangan.objects.all().values(
        'tanggal', 'nomor_order', 'layanan', 'total_harga', 'metode_bayar', 'status'
    )
    return JsonResponse(list(laporan), safe=False)

# Laporan Inventory
def laporan_inventory_view(request):
    return render(request, 'laporan_inventory.html')  # Render halaman HTML

# API untuk data JSON laporan inventory
def laporan_inventory_api(request):
    try:
        # Ambil timezone Asia/Jakarta
        local_tz = pytz.timezone('Asia/Jakarta')
        now = datetime.now(local_tz)

        # Rentang waktu untuk perhitungan
        start_of_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_yesterday = start_of_today - timedelta(days=1)
        end_of_yesterday = start_of_today - timedelta(microseconds=1)
        start_of_week = start_of_today - timedelta(days=7)
        start_of_month = start_of_today - timedelta(days=30)

        # Hitung total item terjual berdasarkan periode
        total_today = 0
        total_yesterday = 0
        total_week = 0
        total_month = 0

        # Ambil semua pesanan
        pesanan_list = Pesanan.objects.all()

        # Ambil data menu untuk mencocokkan SKU
        menu_items = MenuItem.objects.all()
        menu_item_dict = {item.nama_item.strip().lower(): item.sku for item in menu_items}

        laporan_data = []

        # Proses setiap pesanan untuk menghitung total dan menyusun laporan
        for pesanan_obj in pesanan_list:
            pesanan_data = json.loads(pesanan_obj.pesanan)  # Decode data JSON pesanan
            tanggal = localtime(pesanan_obj.tanggal)  # Pastikan tanggal sesuai timezone
            nomor_order = pesanan_obj.nomor_order

            for item in pesanan_data:
                nama_item = item.get('nama_item', '-').strip().lower()
                jumlah_terjual = int(item.get('jumlah', 0))

                # Hitung total berdasarkan periode
                if tanggal >= start_of_today:
                    total_today += jumlah_terjual
                if start_of_yesterday <= tanggal <= end_of_yesterday:
                    total_yesterday += jumlah_terjual
                if tanggal >= start_of_week:
                    total_week += jumlah_terjual
                if tanggal >= start_of_month:
                    total_month += jumlah_terjual

                # Dapatkan SKU dari dictionary menu_item
                sku = menu_item_dict.get(nama_item, '-')

                # Masukkan data ke laporan
                laporan_data.append({
                    'tanggal': tanggal.strftime('%d-%m-%Y %H:%M'),  # Format tanggal
                    'nomor_order': nomor_order,
                    'sku': sku,  # SKU dari tabel MenuItem
                    'nama_item': item.get('nama_item', '-'),
                    'terjual': jumlah_terjual,
                })
                
        # Log untuk debugging
        print("Total Today:", total_today)
        print("Total Yesterday:", total_yesterday)
        print("Total Week:", total_week)
        print("Total Month:", total_month)

        # Kirimkan data dalam format JSON
        return JsonResponse({
            'inventory': laporan_data,
            'total_today': total_today,
            'total_yesterday': total_yesterday,
            'total_week': total_week,
            'total_month': total_month,
        }, safe=False)
    except Exception as e:
        logger.error(f"Error fetching inventory data: {e}")
        return JsonResponse({'error': str(e)}, status=500)

#API Dashboard
def api_billing_data(request):
    try:
        # Ambil waktu sekarang
        current_time = localtime(now())

        # Hitung total pendapatan Hari Ini
        today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = current_time.replace(hour=23, minute=59, second=59, microsecond=999999)
        today_total = Pesanan.objects.filter(tanggal__range=(today_start, today_end)).aggregate(
            total=Sum('total_harga')
        )['total'] or 0

        # Hitung total pendapatan Minggu Ini (7 hari terakhir)
        week_start = current_time - timedelta(days=7)
        week_total = Pesanan.objects.filter(tanggal__gte=week_start).aggregate(
            total=Sum('total_harga')
        )['total'] or 0

        # Hitung total pendapatan Bulan Ini (30 hari terakhir)
        month_start = current_time - timedelta(days=30)
        month_total = Pesanan.objects.filter(tanggal__gte=month_start).aggregate(
            total=Sum('total_harga')
        )['total'] or 0

        # Kirimkan data dalam format JSON
        return JsonResponse({
            'today_total': today_total,
            'week_total': week_total,
            'month_total': month_total,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
