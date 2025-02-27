from django.db import models

class MenuItem(models.Model):  # Model ini harus ada
    idmenu = models.AutoField(primary_key=True)  # Primary key tabel
    sku = models.CharField(max_length=50, unique=True)
    nama_item = models.CharField(max_length=100)
    harga = models.DecimalField(max_digits=10, decimal_places=2)
    kategori = models.CharField(max_length=100)
    stok_saat_ini = models.IntegerField(default=0)  # Kolom baru menggantikan `stok`
    stok_terjual = models.IntegerField(default=0)  # Kolom baru
    gambar = models.URLField(max_length=300, blank=True, null=True)  # URL gambar

    class Meta:
        db_table = 'menu_item'  # Menggunakan tabel database yang sudah ada

    def __str__(self):
        return self.nama_item

class StokLog(models.Model):
    sku = models.CharField(max_length=50)
    stok_awal = models.IntegerField()
    stok_terjual = models.IntegerField()
    stok_akhir = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
