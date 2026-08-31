from django.contrib import admin
from .models import User, ProfilPT, ProfilKlien


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'role', 'is_active', 'date_joined')
    list_filter  = ('role', 'is_active')
    search_fields= ('username',)


@admin.register(ProfilPT)
class ProfilPTAdmin(admin.ModelAdmin):
    list_display = ('nama_lengkap', 'spesialisasi', 'user')
    search_fields= ('nama_lengkap',)


@admin.register(ProfilKlien)
class ProfilKlienAdmin(admin.ModelAdmin):
    list_display = ('nama_lengkap', 'user', 'pt', 'berat_badan')
    list_filter  = ('pt',)
    search_fields= ('nama_lengkap',)
