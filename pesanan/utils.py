import random
import string
from datetime import datetime
from django.db import transaction
from pesanan.models import Pesanan, PesananDetail
from menu.models import MenuItem
import logging
import json


logger = logging.getLogger(__name__)

def generate_order_number():
    """Generate a unique order number."""
    prefix = "ORD"
    unique_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"{prefix}-{unique_id}"

# Fungsi untuk menghitung total jumlah item dan harga
def calculate_totals(pesanan):
    total_harga = 0
    total_jumlah = 0
    for item in pesanan:
        try:
            # Pastikan harga dalam bentuk float
            harga_item = float(item.get('harga', 0))
            jumlah = int(item.get('jumlah', 0))
            total_harga += harga_item * jumlah
            total_jumlah += jumlah
        except ValueError:
            raise ValueError("Harga atau jumlah tidak valid.")
    return total_jumlah, total_harga

# Fungsi untuk menyimpan pesanan ke database
def save_order(data, nomor_order):
    try:
        with transaction.atomic():
            jumlah, total_harga = calculate_totals(data['pesanan'])  # Hitung ulang total di backend
            pesanan_obj = Pesanan.objects.create(
                nomor_order=nomor_order,
                jumlah=jumlah,
                nama_pelanggan=data['nama_pelanggan'],
                tanggal=datetime.now(),
                layanan=data['layanan'],
                pesanan=json.dumps(data['pesanan']) if data.get('pesanan') else "[]",
                total_harga=round(total_harga),  # Simpan total harga yang dihitung ulang
                metode_bayar=data.get('metode_bayar'),
                status='Belum Bayar',
                status_pesanan='-',  # Set status pesanan default
                stok_terupdate=True
            )
            logger.info(f"Pesanan berhasil disimpan: {pesanan_obj}")

            # Simpan detail pesanan
            for item in data['pesanan']:
                sku = item.get('sku')  # Ambil SKU dari data item
                nama_item = item.get('nama_item', 'Unknown Item')  # Default jika tidak ada
                jumlah = int(item.get('jumlah', 0))
                # Periksa tipe data harga
                if isinstance(item['harga'], str):
                    harga_item = float(item['harga'].replace('Rp', '').strip())
                else:
                    harga_item = float(item['harga'])  # Jika sudah berupa angka
                
                PesananDetail.objects.create(
                    pesanan=pesanan_obj,
                    nama_item=item['nama_item'],
                    jumlah=int(item['jumlah']),
                    harga=item['harga']  # Harga langsung dari integer
                )

                # Kurangi stok jika SKU valid
                if sku:
                    menu_item = MenuItem.objects.filter(sku=sku).first()
                    if menu_item:
                        stok_awal = menu_item.stok_saat_ini
                        menu_item.stok_saat_ini = max(menu_item.stok_saat_ini - jumlah, 0)
                        menu_item.stok_terjual += jumlah
                        menu_item.save()
                        logger.info(f"Stok diperbarui untuk SKU={sku}: {stok_awal} -> {menu_item.stok_saat_ini}")
                    else:
                        logger.warning(f"SKU {sku} tidak ditemukan dalam tabel menu_item!")

            return pesanan_obj
    except Exception as e:
        logger.error(f"Error saat menyimpan pesanan: {e}")
        raise