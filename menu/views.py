from django.shortcuts import render, redirect, get_object_or_404
from django.db import connection  # Untuk koneksi ke MySQL
from django.core.files.storage import FileSystemStorage  # Untuk mengelola file upload
from .models import MenuItem  # Pastikan menggunakan jalur yang benar
from rest_framework.generics import ListAPIView, RetrieveAPIView
from .serializers import MenuItemSerializer
from rest_framework import serializers
from laporan.models import LaporanInventory
from django.db.models import Sum, F
from datetime import datetime
from django.views.decorators.cache import never_cache
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.conf import settings
import requests

@never_cache
@login_required

def menu_view(request):
    # Ambil data dari tabel menu_item
    menu_items = MenuItem.objects.all()

    # Format data untuk dikirim ke template
    menu_items_formatted = []
    for item in menu_items:
        menu_items_formatted.append({
            'idmenu': item.idmenu,
            'gambar': item.gambar,
            'sku': item.sku,
            'nama_item': item.nama_item,
            'harga': item.harga,
            'kategori': item.kategori,
            'stok_awal': item.stok_saat_ini + item.stok_terjual,  # Hitung stok awal
            'stok_saat_ini': item.stok_saat_ini,
            'stok_terjual': item.stok_terjual,
        })

    # Kirim data ke template
    return render(request, 'menu/menu.html', {'menu_items': menu_items_formatted})

def tambah_menu(request):
    if request.method == 'POST' and request.FILES.get('gambar'):
        gambar = request.FILES['gambar']
        fs = FileSystemStorage()
        gambar_name = fs.save(gambar.name, gambar)
        gambar_url = fs.url(gambar_name)

        sku = request.POST['sku']
        nama_item = request.POST['nama_item']
        harga = request.POST['harga']
        kategori = ', '.join(request.POST.getlist('kategori'))
        stok_saat_ini = request.POST['stok_saat_ini']  # Ganti `stok` menjadi `stok_saat_ini`

        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO menu_item (gambar, sku, nama_item, harga, kategori, stok_saat_ini, stok_terjual) 
                    VALUES (%s, %s, %s, %s, %s, %s, 0)
                """, [gambar_url, sku, nama_item, harga, kategori, stok_saat_ini])
            print("Data berhasil ditambahkan")
        except Exception as e:
            print("Error saat menambah data:", e)

        save_action = request.POST.get('save_action', 'menu')
        if save_action == 'new':
            return redirect('tambah_menu')

        return redirect('menu')

    return render(request, 'menu/tambah_menu.html')

def edit_menu(request, menu_id):
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT idmenu, gambar, sku, nama_item, harga, kategori, stok_saat_ini, stok_terjual 
            FROM menu_item WHERE idmenu = %s
        """, [menu_id])
        menu_item = cursor.fetchone()

    if not menu_item:
        return redirect('menu')

    if request.method == 'POST':
        sku = request.POST['sku']
        nama_item = request.POST['nama_item']
        harga = request.POST['harga']
        kategori = ', '.join(request.POST.getlist('kategori'))
        stok_saat_ini = request.POST['stok_saat_ini']

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE menu_item 
                SET sku = %s, nama_item = %s, harga = %s, kategori = %s, stok_saat_ini = %s 
                WHERE idmenu = %s
            """, [sku, nama_item, harga, kategori, stok_saat_ini, menu_id])

        return redirect('menu')

    return render(request, 'menu/tambah_menu.html', {
        'menu_item': {
            'idmenu': menu_item[0],
            'gambar': menu_item[1],
            'sku': menu_item[2],
            'nama_item': menu_item[3],
            'harga': menu_item[4],
            'kategori': menu_item[5].split(', '),
            'stok_saat_ini': menu_item[6],
            'stok_terjual': menu_item[7],
        },
        'is_edit': True
    })
    
def delete_menu(request, menu_id):
    # Hapus item dari database berdasarkan ID
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM menu_item WHERE idmenu = %s", [menu_id])
    
    # Redirect kembali ke halaman menu setelah item dihapus
    return redirect('menu')

def update_stok(menu_id, jumlah_terjual):
    print(f"Updating stok for menu_id: {menu_id}, jumlah_terjual: {jumlah_terjual}")
    if jumlah_terjual > 0:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE menu_item 
                SET stok_saat_ini = stok_saat_ini - %s, stok_terjual = stok_terjual + %s 
                WHERE idmenu = %s
            """, [jumlah_terjual, jumlah_terjual, menu_id])

# View untuk menampilkan daftar menu
class MenuItemListView(ListAPIView):
    serializer_class = MenuItemSerializer

    def get_queryset(self):
        return MenuItem.objects.values(
            'idmenu', 'sku', 'nama_item', 'harga', 'kategori', 'stok_saat_ini', 'gambar'
        ).order_by('-idmenu')  # Data terbaru muncul di atas

# View untuk detail menu (opsional)
class MenuItemDetailView(RetrieveAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    lookup_field = 'idmenu'  # Menggunakan `idmenu` sebagai parameter pencarian

class MenuItemSerializer(serializers.ModelSerializer):
    harga = serializers.FloatField()  # Konversi harga menjadi float
    stok_saat_ini = serializers.IntegerField()  # Pastikan stok adalah integer

    gambar = serializers.SerializerMethodField()
    def get_gambar(self, obj):
        if obj.gambar:
            return f"{settings.MEDIA_URL}{obj.gambar}"  # Tambahkan base URL
        return None

    class Meta:
        model = MenuItem
        fields = ['idmenu', 'nama_item', 'harga', 'gambar', 'kategori', 'stok_saat_ini']
