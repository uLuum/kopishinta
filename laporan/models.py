from django.db import models
from menu.models import MenuItem  # Import model MenuItem
from django.utils.timezone import now

class Pesanan(models.Model):
    menu = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name='laporan_pesanan'  # Tambahkan related_name khusus untuk aplikasi laporan
    )
    pesanan = models.JSONField(default=dict)
    tanggal = models.DateField(auto_now_add=True)
    nomor_order = models.CharField(max_length=20)
    layanan = models.CharField(max_length=50)
    total_harga = models.DecimalField(max_digits=10, decimal_places=2)
    status_bayar = models.CharField(
        max_length=10, choices=[('Lunas', 'Lunas'), ('Belum', 'Belum')]
    )
    metode_bayar = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        default=None
    )

    def __str__(self):
        return f"Order {self.nomor_order} - {self.total_harga}"

class LaporanKeuangan(models.Model):
    tanggal = models.DateField(auto_now_add=True)
    nomor_order = models.CharField(max_length=50)
    layanan = models.CharField(max_length=50)
    total_harga = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20)
    metode_bayar = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        default=None
    )

    def __str__(self):
        return f"Laporan {self.nomor_order} ({self.tanggal})"

class LaporanInventory(models.Model):
    sku = models.CharField(max_length=20)  # SKU dari MenuItem
    nama_item = models.CharField(max_length=100)  # Nama item
    jumlah_terjual = models.PositiveIntegerField(default=0)  # Jumlah terjual
    tanggal = models.DateField(auto_now_add=True)  # Tanggal transaksi

    def __str__(self):
        return f"{self.nama_item} - {self.jumlah_terjual} terjual"

