"""
SmartGym AI — Users Models
Custom User dengan field role: admin, pt, klien
"""
from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('pt', 'Personal Trainer'),
        ('klien', 'Klien Gym'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='klien')

    class Meta:
        verbose_name = 'Pengguna'
        verbose_name_plural = 'Daftar Pengguna'

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_pt(self):
        return self.role == 'pt'

    @property
    def is_klien(self):
        return self.role == 'klien'


class ProfilPT(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil_pt')
    nama_lengkap = models.CharField(max_length=100)
    spesialisasi = models.CharField(max_length=100, blank=True, default='')

    class Meta:
        verbose_name = 'Profil Personal Trainer'

    def __str__(self):
        return self.nama_lengkap


class ProfilKlien(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profil_klien')
    pt = models.ForeignKey(
        ProfilPT, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='klien_list'
    )
    nama_lengkap = models.CharField(max_length=100)
    berat_badan = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        verbose_name = 'Profil Klien'

    def __str__(self):
        return self.nama_lengkap
