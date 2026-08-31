"""
SmartGym AI — Sesi Models
MasterGerakan dan SesiLatihan
"""
from django.db import models
from django.conf import settings


class MasterGerakan(models.Model):
    nama_gerakan = models.CharField(max_length=50)
    sudut_maksimal = models.DecimalField(max_digits=5, decimal_places=2, default=90.00)
    wajib_scapular_plane = models.BooleanField(default=True)
    deskripsi = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Master Gerakan'
        verbose_name_plural = 'Master Gerakan'
        ordering = ['nama_gerakan']

    def __str__(self):
        return self.nama_gerakan


class SesiLatihan(models.Model):
    klien = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'klien'},
        related_name='sesi_list'
    )
    gerakan = models.ForeignKey(MasterGerakan, on_delete=models.CASCADE)
    waktu_mulai = models.DateTimeField(auto_now_add=True)
    total_reps = models.IntegerField(default=0)
    total_form_error = models.IntegerField(default=0)
    catatan = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Sesi Latihan'
        verbose_name_plural = 'Riwayat Sesi Latihan'
        ordering = ['-waktu_mulai']

    def __str__(self):
        return f"{self.klien.username} — {self.gerakan.nama_gerakan} — {self.waktu_mulai:%Y-%m-%d %H:%M}"

    @property
    def form_error_rate(self):
        total = self.total_reps + self.total_form_error
        if total == 0:
            return 0.0
        return round(self.total_form_error / total * 100, 1)
