# dashboard/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    # Tambahkan field tambahan jika diperlukan
    bio = models.TextField(null=True, blank=True)

    # Gunakan metode bawaan AbstractUser untuk create_user dan create_superuser
    pass
class Product(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='products/')  # Gambar akan disimpan di 'media/products/'

    def __str__(self):
        return self.name