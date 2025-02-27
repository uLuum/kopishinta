from django.shortcuts import render, redirect, get_object_or_404
from django.db import connection, transaction
from datetime import datetime, timedelta
from django.utils.timezone import get_current_timezone, localtime, now, timedelta
from django.http import JsonResponse, HttpResponse
from io import BytesIO
from .models import Pesanan, PesananDetail
from menu.models import MenuItem
from pesanan.utils import generate_order_number
from django.db.models import F
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.db.models.signals import post_save
from django.dispatch import receiver
from laporan.models import LaporanKeuangan
from .utils import calculate_totals, save_order
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Group
from django.contrib import messages
import pytz
import random
import json
import logging

logger = logging.getLogger(__name__)
@login_required

def menu_view(request):
    # Ambil semua data dari tabel MenuItem
    menu_items = MenuItem.objects.all()

    print(menu_items)  # Debugging: tampilkan data di server log

    # Kirim data QuerySet langsung ke template
    return render(request, 'menu/menu.html', {'menu_items': menu_items})

def pesanan(request):
    search_query = request.GET.get('q', '')  # Ambil parameter pencarian dari query string

    with connection.cursor() as cursor:
        # Jika ada query pencarian
        if search_query:
            cursor.execute("""
            SELECT 
                idorder, nomor_order, nama_pelanggan, layanan, tanggal, total_harga, metode_bayar, status, status_pesanan, pesanan
            FROM pesanan
            WHERE nomor_order LIKE %s OR nama_pelanggan LIKE %s
            ORDER BY tanggal DESC
            """, [f"%{search_query}%", f"%{search_query}%"])
        else:
            cursor.execute("""
            SELECT 
                idorder, nomor_order, nama_pelanggan, layanan, tanggal, total_harga, metode_bayar, status, status_pesanan, pesanan
            FROM pesanan
            ORDER BY tanggal DESC
            """)
        orders = cursor.fetchall()

    # Ambil timezone aplikasi
    local_tz = pytz.timezone('Asia/Jakarta')

    # Buat list untuk menyimpan hasil query
    orders_list = []
    for order in orders:
        # Konversi datetime dari UTC ke timezone lokal
        utc_tanggal = order[4]  # Ambil data tanggal dari database (diasumsikan dalam UTC)
        if utc_tanggal.tzinfo is None:  # Jika tanggal naive
            utc_tanggal = pytz.utc.localize(utc_tanggal)  # Jadikan timezone-aware (UTC)

        # Konversi ke timezone lokal
        local_tanggal = utc_tanggal.astimezone(local_tz)
        formatted_date = local_tanggal.strftime('%d-%m-%Y %H:%M')  # Format sesuai kebutuhan

        # Validasi kolom pesanan (data JSON)
        raw_pesanan = order[9]  # Indeks 9 adalah kolom pesanan
        try:
            pesanan_data = json.loads(raw_pesanan) if raw_pesanan else []  # Gunakan nilai default []
        except json.JSONDecodeError:
            pesanan_data = []  # Gunakan default jika JSON tidak valid
        
        # Format daftar item pesanan dari data JSON
        order_items = ", ".join([f"{item['nama_item']} x{item['jumlah']}" for item in pesanan_data])

        # Tambahkan data ke list orders_list
        orders_list.append({
            'idorder': order[0],
            'nomor_order': order[1],
            'nama_pelanggan': order[2],
            'layanan': order[3],
            'tanggal': formatted_date,
            'total_harga': order[5],
            'metode_bayar': order[6],
            'status': order[7],
            'status_pesanan': order[8],
            'orderData': order_items  # Data pesanan ditambahkan ke dictionary
        })

    # Jika permintaan AJAX, balas dengan JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'orders': orders_list})

    return render(request, 'pesanan/pesanan.html', {'orders': orders_list})

def tambah_order(request):
    print("Masuk ke fungsi tambah_order")  # Debugging
    try:
        # Ambil data menu menggunakan QuerySet Django
        menu_items = MenuItem.objects.all()
        print("Query berhasil dijalankan:", menu_items)  # Debugging
    except Exception as e:
        print("Error saat query:", e)  # Debugging
        menu_items = []

    if not menu_items.exists():
        print("Data menu kosong. Pastikan tabel menu_item memiliki data.")  # Debugging
    else:
        print(f"Jumlah menu yang ditemukan: {menu_items.count()}")
    return render(request, 'pesanan/tambah_order.html', {'menu_items': menu_items})

# Fungsi untuk checkout
@csrf_exempt
def checkout_view(request):
    if request.method == 'POST':
        try:
            # Validasi apakah body kosong
            if not request.body:
                return JsonResponse({'success': False, 'message': 'Body request kosong'}, status=400)
            
            # Ambil data dari request JSON
            data = json.loads(request.body)
            nama_pelanggan = data.get('nama_pelanggan')
            layanan = data.get('layanan')
            pesanan = data.get('pesanan')

            # Validasi input
            if not nama_pelanggan or not layanan or not pesanan:
                return JsonResponse({'success': False, 'message': 'Data tidak lengkap'}, status=400)
            
            # Validasi harga
            for item in data.get('pesanan', []):
                try:
                    # Konversi harga menjadi float jika dalam bentuk string
                    item['harga'] = float(item['harga'])
                except ValueError:
                    return JsonResponse({'success': False, 'message': 'Harga harus berupa angka'}, status=400)

            # Hitung jumlah item dan total harga
            jumlah, total_harga = calculate_totals(pesanan)

            # Generate nomor order
            nomor_order = f"ORD-{datetime.now().strftime('%H%M%S')}"

            # Simpan pesanan ke database
            save_order({
                'nama_pelanggan': nama_pelanggan,
                'layanan': layanan,
                'pesanan': pesanan,
                'jumlah': jumlah,
                'total_harga': total_harga,
                'metode_bayar': data.get('metode_bayar')
            }, nomor_order)

            # Tambahkan tanggal ke ringkasan pesanan
            tanggal_pesanan = datetime.now().strftime('%d-%m-%Y %H:%M')

            # Simpan ringkasan pesanan di session
            request.session['summary'] = {
                'nomor_order': nomor_order,
                'nama_pelanggan': nama_pelanggan,
                'layanan': layanan,
                'pesanan': pesanan,
                'jumlah': jumlah,
                'metode_bayar': data.get('metode_bayar'),
                'total_harga': total_harga,
                'tanggal': tanggal_pesanan
            }
            
            return JsonResponse({
                'success': True,
                'message': 'Pesanan berhasil disimpan',
                'redirect_url': reverse('checkout_summary'),
                    'order_summary': {
                        'nomor_order': nomor_order,
                        'nama_pelanggan': nama_pelanggan,
                        'layanan': layanan,
                        'pesanan': pesanan,
                        'jumlah': jumlah,
                        'total_harga': total_harga,
                        'tanggal': tanggal_pesanan
                    }
            })

        except Exception as e:
            print("Error saat menyimpan pesanan:", e)
            return JsonResponse({'success': False, 'message': 'Terjadi kesalahan pada server'}, status=500)

    return JsonResponse({'success': False, 'message': 'Metode request tidak valid'}, status=400)

def checkout_summary(request):
    # Ambil data ringkasan pesanan dari session (opsional)
    summary = request.session.get('summary', {})

    # Cek apakah nomor_order tersedia di sesi
    nomor_order = request.session.pop('nomor_order', None)  # Ambil dan hapus nomor_order dari sesi
    if not nomor_order:
        # Jika tidak ada di sesi, ambil dari query string
        nomor_order = request.GET.get('nomor_order')
        if not nomor_order:
            messages.error(request, "Nomor order tidak ditemukan.")
            return redirect('pesanan')

    try:
        # Ambil data pesanan berdasarkan nomor_order
        pesanan = Pesanan.objects.filter(nomor_order=nomor_order).first()
        if not summary:
            messages.error(request, "Pesanan tidak ditemukan.")
            return redirect('pesanan')

        # Parse data pesanan
        pesanan_items = json.loads(pesanan.pesanan) if pesanan.pesanan else []
        
        # Hitung total jumlah item
        jumlah_items = sum(item['jumlah'] for item in pesanan_items)
        
        # Format data summary untuk template
        summary = {
            'nomor_order': pesanan.nomor_order,
            'nama_pelanggan': pesanan.nama_pelanggan,
            'layanan': pesanan.layanan,
            'pesanan': pesanan_items,
            'jumlah': jumlah_items,  # Tambahkan total item
            'total_harga': pesanan.total_harga,  # Simpan sebagai float untuk kompatibilitas
            'tanggal': pesanan.tanggal.strftime('%d-%m-%Y %H:%M'),
        }

        # Debug log untuk memastikan data terkirim ke template
        print("Summary data:", summary)

        return render(request, 'pesanan/checkout.html', {'summary': summary})

    except Exception as e:
        print(f"Error saat memuat checkout: {e}")
        messages.error(request, "Terjadi kesalahan saat memuat halaman checkout.")
        return redirect('pesanan')


# Fungsi untuk memperbarui status menjadi "Lunas"
def mark_as_paid(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nomor_order = data.get('nomor_order')

            if not nomor_order:
                return JsonResponse({'success': False, 'message': 'Nomor order tidak ditemukan'}, status=400)

            pesanan = get_object_or_404(Pesanan, nomor_order=nomor_order)

            if pesanan.stok_terupdate:
                # Stok sudah diperbarui, cukup ubah status
                pesanan.status = 'Lunas'
                # Jika status_pesanan masih "-", ubah menjadi "Baru"
                if pesanan.status_pesanan == "-":
                    pesanan.status_pesanan = "Baru"
                pesanan.save()
                return JsonResponse({'success': True, 'message': 'Pesanan telah lunas.'})
            else:
                return JsonResponse({'success': False, 'message': 'Stok belum diperbarui. Lakukan validasi ulang pesanan.'})

            return JsonResponse({'success': True, 'message': 'Pesanan telah lunas dan stok diperbarui.'})
        except Exception as e:
            print(f"Error marking as paid: {e}")
            return JsonResponse({'success': False, 'message': 'Terjadi kesalahan pada server'}, status=500)
    return JsonResponse({'success': False, 'message': 'Metode request tidak valid'}, status=400)

# Fungsi untuk memperbarui metode_bayar
def update_payment_method(request):
    if request.method == 'POST':
        try:
            # Ambil data dari request JSON
            data = json.loads(request.body)
            nomor_order = data.get('nomor_order')
            metode_bayar = data.get('metode_bayar')
            nominal_pembayaran = data.get('nominal_pembayaran')  # Ambil nominal pembayaran dari request

            if not nomor_order or not metode_bayar or nominal_pembayaran is None:
                return JsonResponse({'success': False, 'message': 'Data tidak lengkap'}, status=400)

            # Cari pesanan berdasarkan nomor_order
            pesanan = get_object_or_404(Pesanan, nomor_order=nomor_order)

            # Hitung kembalian
            total_harga = pesanan.total_harga
            if nominal_pembayaran < total_harga:
                return JsonResponse({'success': False, 'message': 'Nominal pembayaran tidak mencukupi'}, status=400)

            kembalian = nominal_pembayaran - total_harga

            # Perbarui metode_bayar, total_harga, dan kembalian
            pesanan.metode_bayar = metode_bayar
            pesanan.total_harga = total_harga  # Simpan nominal pembayaran ke total_harga
            pesanan.save()
            
            return JsonResponse({'success': True, 'message': 'Metode bayar berhasil diperbarui'})
        except Exception as e:
            print("Error saat memperbarui metode bayar:", e)
            return JsonResponse({'success': False, 'message': 'Terjadi kesalahan pada server'}, status=500)

    return JsonResponse({'success': False, 'message': 'Metode request tidak valid'}, status=400)

@csrf_exempt
def delete_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nomor_order = data.get('nomor_order')

            if not nomor_order:
                return JsonResponse({'success': False, 'message': 'Nomor order tidak ditemukan'}, status=400)

            # Cari pesanan berdasarkan nomor_order dan hapus
            pesanan = Pesanan.objects.filter(nomor_order=nomor_order).first()
            if pesanan:
                pesanan.delete()
                return JsonResponse({'success': True, 'message': 'Pesanan berhasil dibatalkan.'})
            else:
                return JsonResponse({'success': False, 'message': 'Pesanan tidak ditemukan.'}, status=404)
        except Exception as e:
            print("Error saat menghapus pesanan:", e)
            return JsonResponse({'success': False, 'message': 'Terjadi kesalahan pada server.'}, status=500)

    return JsonResponse({'success': False, 'message': 'Metode request tidak valid.'}, status=400)

def sinkronisasi_laporan(pesanan):
    laporan = LaporanKeuangan.objects.create(
        tanggal=pesanan.tanggal,
        nomor_order=pesanan.nomor_order,
        total_harga=pesanan.total_harga,
        status=pesanan.status
    )
    laporan.save()


def perbaiki_format_json():
    with connection.cursor() as cursor:
        # Ambil semua data JSON yang salah
        cursor.execute("SELECT idorder, pesanan FROM pesanan WHERE pesanan LIKE '%null%';")
        results = cursor.fetchall()

        for result in results:
            idorder = result[0]
            pesanan_raw = result[1]

            try:
                # Parse JSON yang salah
                pesanan_data = json.loads(pesanan_raw)

                # Perbaiki data JSON
                formatted_data = []
                for item in pesanan_data:
                    formatted_data.append({
                        "idmenu": int(item.get("idmenu", 0)),  # Nilai default 0 jika null
                        "nama_item": item.get("nama_item", "Unknown Item"),  # Nama default
                        "jumlah": int(item.get("jumlah", 1)),  # Default jumlah 1
                        "harga": item.get("harga", "Rp 0")  # Harga default
                    })

                # Simpan kembali JSON yang sudah diformat
                formatted_json = json.dumps(formatted_data)

                # Update data di database
                cursor.execute(
                    "UPDATE pesanan SET pesanan = %s WHERE idorder = %s",
                    [formatted_json, idorder]
                )
                print(f"Pesanan ID {idorder} berhasil diperbaiki.")
            except Exception as e:
                print(f"Error memperbaiki pesanan ID {idorder}: {e}")

def update_stok_checkout(sku, jumlah_terjual):
    try:
        # Ambil item berdasarkan SKU
        menu_item = MenuItem.objects.get(sku=sku)

        # Hitung stok akhir
        stok_awal = menu_item.stok_saat_ini
        stok_akhir = max(stok_awal - jumlah_terjual, 0)

        # Perbarui stok di database
        menu_item.stok_saat_ini = stok_akhir
        menu_item.stok_terjual += jumlah_terjual
        menu_item.save()

        # Log perubahan stok (opsional, bisa dihapus jika tidak diperlukan)
        print(f"Stok diperbarui: SKU={sku}, Stok Awal={stok_awal}, Jumlah Terjual={jumlah_terjual}, Stok Akhir={stok_akhir}")
    except MenuItem.DoesNotExist:
        print(f"SKU {sku} tidak ditemukan dalam tabel menu_item.")

@csrf_exempt
def get_orders(request):
    try:
        today_start = localtime(now()).replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = localtime(now()).replace(hour=23, minute=59, second=59, microsecond=999999)

        pesanan_baru = Pesanan.objects.filter(
            status="Lunas",
            status_pesanan__in=["Baru", "Diproses"],
            tanggal__range=[today_start, today_end]
        ).values()

        pesanan_disajikan = Pesanan.objects.filter(
            status_pesanan="Disajikan",
            tanggal__range=[today_start, today_end]
        ).values()

        orders_list = []
        for order in list(pesanan_baru) + list(pesanan_disajikan):  # Gabungkan pesanan
            try:
                pesanan_parsed = json.loads(order['pesanan']) if isinstance(order['pesanan'], str) else order['pesanan']
            except json.JSONDecodeError:
                pesanan_parsed = []  # Handle parsing error

            orders_list.append({
                'idorder': order['idorder'],
                'nomor_order': order['nomor_order'] or "No Order",
                'nama_pelanggan': order['nama_pelanggan'] or "Unknown",
                'layanan': order['layanan'] or "Unknown",
                'status_pesanan': order['status_pesanan'],  # Ensure this is correctly formatted
                'pesanan': pesanan_parsed,
            })

        return JsonResponse({"success": True, "orders": orders_list})

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)

@csrf_exempt
def update_order_status(request):    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            nomor_order = data.get("nomor_order")
            status_pesanan_baru = data.get("status_pesanan")  

            pesanan = Pesanan.objects.filter(nomor_order=nomor_order).first()
            if pesanan:
                if pesanan.status_pesanan == "Diproses" and status_pesanan_baru == "Disajikan":
                    pesanan.status_pesanan = "Disajikan"  # Ubah status ke "Disajikan" terlebih dahulu
                elif pesanan.status_pesanan == "Disajikan" and status_pesanan_baru == "Selesai":
                    pesanan.delete()  # Hapus hanya jika sudah "Disajikan"
                else:
                    pesanan.status_pesanan = status_pesanan_baru
                
                pesanan.save()
                return JsonResponse({"success": True, "message": f"Status pesanan diperbarui ke {status_pesanan_baru}"})
            
            return JsonResponse({"success": False, "message": "Pesanan tidak ditemukan"}, status=404)
        
        except Exception as e:
            return JsonResponse({"success": False, "message": f"Error: {str(e)}"}, status=500)

    return JsonResponse({"message": "Metode tidak diperbolehkan"}, status=405)
