from django.contrib import admin
from .models import MasterGerakan, SesiLatihan


@admin.register(MasterGerakan)
class MasterGerakanAdmin(admin.ModelAdmin):
    list_display = ('nama_gerakan', 'sudut_maksimal', 'wajib_scapular_plane')


@admin.register(SesiLatihan)
class SesiLatihanAdmin(admin.ModelAdmin):
    list_display = ('klien', 'gerakan', 'waktu_mulai', 'total_reps', 'total_form_error')
    list_filter  = ('gerakan', 'waktu_mulai')
    date_hierarchy = 'waktu_mulai'
