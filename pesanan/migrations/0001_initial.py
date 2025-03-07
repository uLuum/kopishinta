# Generated by Django 5.1.3 on 2025-01-23 12:29

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='MenuItem',
            fields=[
                ('idmenu', models.AutoField(primary_key=True, serialize=False)),
                ('sku', models.CharField(max_length=50, unique=True)),
                ('nama_item', models.CharField(max_length=100)),
                ('harga', models.DecimalField(decimal_places=2, max_digits=10)),
                ('kategori', models.CharField(max_length=100)),
                ('stok', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Pesanan',
            fields=[
                ('idorder', models.AutoField(primary_key=True, serialize=False)),
                ('nomor_order', models.CharField(max_length=50, unique=True)),
                ('jumlah', models.IntegerField()),
                ('nama_pelanggan', models.CharField(max_length=100)),
                ('tanggal', models.DateTimeField(auto_now_add=True)),
                ('layanan', models.CharField(max_length=50)),
                ('pesanan', models.TextField()),
                ('total_harga', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('metode_bayar', models.CharField(blank=True, default=None, max_length=50, null=True)),
                ('status', models.CharField(max_length=50)),
                ('menu', models.ForeignKey(db_column='idmenu', on_delete=django.db.models.deletion.CASCADE, to='pesanan.menuitem')),
            ],
            options={
                'db_table': 'pesanan',
            },
        ),
        migrations.CreateModel(
            name='PesananDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nama_item', models.CharField(max_length=255)),
                ('jumlah', models.IntegerField()),
                ('harga', models.DecimalField(decimal_places=2, max_digits=10)),
                ('pesanan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pesanan.pesanan')),
            ],
            options={
                'db_table': 'pesanan_detail',
            },
        ),
    ]
