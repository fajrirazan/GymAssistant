from django.urls import path
from . import views

urlpatterns = [
    path('simpan-sesi/', views.simpan_sesi, name='simpan_sesi'),
    path('riwayat/<int:id_klien>/', views.get_riwayat, name='get_riwayat'),
    path('statistik/<int:id_klien>/', views.get_statistik, name='get_statistik'),
    path('gerakan/', views.get_gerakan, name='get_gerakan'),
]
