"""
SmartGym AI — Dashboard Views
Admin, PT, Klien, dan halaman AI Training
"""
import json
from functools import wraps
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model

from users.models import ProfilPT, ProfilKlien
from sesi.models import MasterGerakan, SesiLatihan

User = get_user_model()


# ─── DECORATORS ROLE ─────────────────────────────────────────────────────────

def role_required(*roles):
    def decorator(func):
        @wraps(func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role not in roles:
                messages.error(request, 'Akses ditolak. Role tidak sesuai.')
                return redirect('login')
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


# ─── ROOT REDIRECT ────────────────────────────────────────────────────────────

@login_required
def index(request):
    role_map = {'admin': 'admin_dashboard', 'pt': 'pt_dashboard', 'klien': 'klien_dashboard'}
    return redirect(role_map.get(request.user.role, 'login'))


# ─── KLIEN VIEWS ─────────────────────────────────────────────────────────────

@role_required('klien')
def klien_dashboard(request):
    klien = request.user
    try:
        profil = klien.profil_klien
        pt = profil.pt
    except ProfilKlien.DoesNotExist:
        profil = None
        pt = None

    riwayat = SesiLatihan.objects.filter(klien=klien).select_related('gerakan').order_by('-waktu_mulai')[:10]

    context = {
        'user': klien,
        'profil': profil,
        'pt': pt,
        'riwayat': riwayat,
        'total_sesi': SesiLatihan.objects.filter(klien=klien).count(),
    }
    return render(request, 'klien/dashboard.html', context)


@role_required('klien')
def klien_latihan(request):
    gerakan_list = MasterGerakan.objects.all()
    context = {
        'user': request.user,
        'gerakan_list': gerakan_list,
        'user_id': request.user.pk,
    }
    return render(request, 'klien/latihan.html', context)


# ─── PT VIEWS ─────────────────────────────────────────────────────────────────

@role_required('pt', 'admin')
def pt_dashboard(request):
    try:
        profil_pt = request.user.profil_pt
        klien_list = ProfilKlien.objects.filter(pt=profil_pt).select_related('user')
    except ProfilPT.DoesNotExist:
        profil_pt = None
        klien_list = []

    context = {
        'user': request.user,
        'profil_pt': profil_pt,
        'klien_list': klien_list,
        'total_klien': len(klien_list),
    }
    return render(request, 'pt/dashboard.html', context)


# ─── ADMIN VIEWS ─────────────────────────────────────────────────────────────

@role_required('admin')
def admin_dashboard(request):
    all_users = User.objects.all().order_by('role', 'username')
    all_pt = ProfilPT.objects.select_related('user').all()
    all_klien = ProfilKlien.objects.select_related('user', 'pt').all()
    gerakan_list = MasterGerakan.objects.all()

    context = {
        'user': request.user,
        'all_users': all_users,
        'all_pt': all_pt,
        'all_klien': all_klien,
        'gerakan_list': gerakan_list,
        'total_users': all_users.count(),
        'total_sesi': SesiLatihan.objects.count(),
    }
    return render(request, 'admin/dashboard.html', context)


# ─── ADMIN API ENDPOINTS ──────────────────────────────────────────────────────

@role_required('admin')
@require_http_methods(['POST'])
def admin_tambah_pt(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'pesan': 'JSON tidak valid.'}, status=400)

    username = data.get('username', '').strip()
    password = data.get('password', '')
    nama = data.get('nama', '').strip()
    spesialisasi = data.get('spesialisasi', '').strip()

    if not all([username, password, nama]):
        return JsonResponse({'status': 'error', 'pesan': 'Username, password, nama wajib diisi.'}, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({'status': 'error', 'pesan': f"Username '{username}' sudah digunakan."}, status=400)

    user = User.objects.create_user(username=username, password=password, role='pt')
    ProfilPT.objects.create(user=user, nama_lengkap=nama, spesialisasi=spesialisasi)
    return JsonResponse({'status': 'ok', 'pesan': f"PT '{nama}' berhasil ditambahkan.", 'id_user': user.pk})


@role_required('admin')
@require_http_methods(['POST'])
def admin_tambah_klien(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'pesan': 'JSON tidak valid.'}, status=400)

    username = data.get('username', '').strip()
    password = data.get('password', '')
    nama = data.get('nama', '').strip()
    berat = data.get('berat_badan')
    id_pt = data.get('id_pt')

    if not all([username, password, nama]):
        return JsonResponse({'status': 'error', 'pesan': 'Username, password, nama wajib diisi.'}, status=400)

    if User.objects.filter(username=username).exists():
        return JsonResponse({'status': 'error', 'pesan': f"Username '{username}' sudah digunakan."}, status=400)

    pt_profil = None
    if id_pt:
        try:
            pt_profil = ProfilPT.objects.get(pk=id_pt)
        except ProfilPT.DoesNotExist:
            pass

    user = User.objects.create_user(username=username, password=password, role='klien')
    ProfilKlien.objects.create(user=user, nama_lengkap=nama, berat_badan=berat, pt=pt_profil)
    return JsonResponse({'status': 'ok', 'pesan': f"Klien '{nama}' berhasil ditambahkan.", 'id_user': user.pk})


@role_required('admin')
@require_http_methods(['DELETE'])
def admin_hapus_user(request, id_user):
    try:
        user = User.objects.get(pk=id_user)
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'pesan': 'User tidak ditemukan.'}, status=404)

    if user.role == 'admin':
        return JsonResponse({'status': 'error', 'pesan': 'Tidak bisa menghapus akun Admin.'}, status=400)

    username = user.username
    user.delete()
    return JsonResponse({'status': 'ok', 'pesan': f"User '{username}' berhasil dihapus."})


@role_required('admin')
@require_http_methods(['PATCH'])
def admin_toggle_user(request, id_user):
    try:
        user = User.objects.get(pk=id_user)
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'pesan': 'User tidak ditemukan.'}, status=404)

    if user.role == 'admin':
        return JsonResponse({'status': 'error', 'pesan': 'Status Admin tidak dapat diubah.'}, status=400)

    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    status_text = 'diaktifkan' if user.is_active else 'dinonaktifkan'
    return JsonResponse({'status': 'ok', 'pesan': f"Akun '{user.username}' berhasil {status_text}.", 'is_active': user.is_active})


@role_required('admin')
@require_http_methods(['POST'])
def admin_assign_pt(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'pesan': 'JSON tidak valid.'}, status=400)

    id_klien_profil = data.get('id_klien')
    id_pt_profil = data.get('id_pt')

    try:
        klien = ProfilKlien.objects.get(pk=id_klien_profil)
        pt = ProfilPT.objects.get(pk=id_pt_profil)
    except (ProfilKlien.DoesNotExist, ProfilPT.DoesNotExist):
        return JsonResponse({'status': 'error', 'pesan': 'Data klien atau PT tidak ditemukan.'}, status=404)

    klien.pt = pt
    klien.save(update_fields=['pt'])
    return JsonResponse({'status': 'ok', 'pesan': f"PT '{pt.nama_lengkap}' berhasil di-assign ke klien '{klien.nama_lengkap}'."})


@role_required('admin')
@require_http_methods(['POST'])
def admin_update_gerakan(request, id_gerakan):
    try:
        gerakan = MasterGerakan.objects.get(pk=id_gerakan)
        data = json.loads(request.body)
    except (MasterGerakan.DoesNotExist, json.JSONDecodeError) as e:
        return JsonResponse({'status': 'error', 'pesan': str(e)}, status=400)

    sudut_maks = float(data.get('sudut_maksimal', gerakan.sudut_maksimal))
    wajib_scapular = bool(data.get('wajib_scapular_plane', gerakan.wajib_scapular_plane))

    if not (0 < sudut_maks <= 180):
        return JsonResponse({'status': 'error', 'pesan': 'Sudut harus antara 1–180.'}, status=400)

    gerakan.sudut_maksimal = sudut_maks
    gerakan.wajib_scapular_plane = wajib_scapular
    gerakan.save()
    return JsonResponse({'status': 'ok', 'pesan': 'Parameter biomekanika diperbarui.'})
