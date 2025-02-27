from django.db import models
from menu.models import MenuItem  # Import model MenuItem
from django.utils.timezone import now
        
class Pesanan(models.Model):
    idorder = models.AutoField(primary_key=True)  # Primary key adalah idorder
    nomor_order = models.CharField(max_length=50, unique=True)
    menu = models.ForeignKey(MenuItem, on_delete=models.CASCADE, db_column='idmenu')  # Sesuaikan dengan nama kolom
    jumlah = models.IntegerField()
    nama_pelanggan = models.CharField(max_length=100)
    tanggal = models.DateTimeField(auto_now_add=True)
    layanan = models.CharField(max_length=50)
    pesanan = models.TextField()
    total_harga = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    metode_bayar = models.CharField(
        max_length=50,
        null=True,  # Boleh kosong
        blank=True,
        default=None  # Default None jika tidak diisi
    )
    status_pesanan = models.CharField(
        max_length=50,
        choices=[
            ('-', '-'),  # Status pesanan default jika belum dibayar
            ('Baru', 'Baru'),
            ('Diproses', 'Diproses'),
            ('Disajikan', 'Disajikan')
        ],
        default='-'  # status default
    ) #status proses pesanan

    status = models.CharField(max_length=50) # Fungsi status bayara Lunas atau belum bayar
    stok_terupdate = models.BooleanField(default=False)  # Tambahkan kolom ini
    
    class Meta:
        db_table = 'pesanan'  # Gunakan nama tabel yang sudah ada di database

    def _str_(self):
        return f"{self.nomor_order} - {self.nama_pelanggan}"

class PesananDetail(models.Model):
    pesanan = models.ForeignKey('Pesanan', on_delete=models.CASCADE)
    nama_item = models.CharField(max_length=255)
    jumlah = models.IntegerField()
    harga = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'pesanan_detail'  # Gunakan nama tabel yang sudah ada di database

    def subtotal(self):
        return self.jumlah * self.harga