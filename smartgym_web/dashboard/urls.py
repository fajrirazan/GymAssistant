from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # Klien
    path('klien/', views.klien_dashboard, name='klien_dashboard'),
    path('klien/latihan/', views.klien_latihan, name='klien_latihan'),
    # PT
    path('pt/', views.pt_dashboard, name='pt_dashboard'),
    # Admin
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/pt/tambah/', views.admin_tambah_pt, name='admin_tambah_pt'),
    path('admin-panel/klien/tambah/', views.admin_tambah_klien, name='admin_tambah_klien'),
    path('admin-panel/users/<int:id_user>/hapus/', views.admin_hapus_user, name='admin_hapus_user'),
    path('admin-panel/users/<int:id_user>/toggle/', views.admin_toggle_user, name='admin_toggle_user'),
    path('admin-panel/assign-pt/', views.admin_assign_pt, name='admin_assign_pt'),
    path('admin-panel/gerakan/<int:id_gerakan>/update/', views.admin_update_gerakan, name='admin_update_gerakan'),
]
