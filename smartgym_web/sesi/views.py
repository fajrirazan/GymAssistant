"""
SmartGym AI — Sesi REST API Views
Endpoint: simpan sesi, riwayat, statistik, master gerakan
"""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncDate

from .models import SesiLatihan, MasterGerakan
from users.models import ProfilKlien


def _json_error(msg, status=400):
    return JsonResponse({'status': 'error', 'pesan': msg}, status=status)


def _json_ok(data=None, pesan='OK'):
    resp = {'status': 'ok', 'pesan': pesan}
    if data is not None:
        resp['data'] = data
    return JsonResponse(resp)


# ─── POST /api/simpan-sesi/ ───────────────────────────────────────────────────
@login_required
@require_http_methods(['POST'])
def simpan_sesi(request):
    """Terima JSON dari JS frontend dan simpan ke database."""
    if request.user.role not in ('klien', 'admin'):
        return _json_error('Akses ditolak.', 403)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return _json_error('Format JSON tidak valid.')

    gerakan_id = body.get('gerakan_id')
    reps = body.get('reps', 0)
    errors = body.get('errors', 0)
    catatan = body.get('catatan', '')

    if not gerakan_id:
        return _json_error('Field gerakan_id wajib diisi.')

    try:
        gerakan = MasterGerakan.objects.get(pk=gerakan_id)
    except MasterGerakan.DoesNotExist:
        return _json_error(f'Gerakan dengan id {gerakan_id} tidak ditemukan.', 404)

    # Resolusi id_klien: admin bisa kirim atas nama klien, klien hanya diri sendiri
    if request.user.role == 'admin':
        klien_id = body.get('klien_id', request.user.pk)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            klien_user = User.objects.get(pk=klien_id, role='klien')
        except User.DoesNotExist:
            return _json_error('Data klien tidak ditemukan.', 404)
    else:
        klien_user = request.user

    sesi = SesiLatihan.objects.create(
        klien=klien_user,
        gerakan=gerakan,
        total_reps=int(reps),
        total_form_error=int(errors),
        catatan=catatan,
    )

    return _json_ok({'id_sesi': sesi.pk}, 'Sesi berhasil disimpan.')


# ─── GET /api/riwayat/<id_klien>/ ────────────────────────────────────────────
@login_required
@require_http_methods(['GET'])
def get_riwayat(request, id_klien):
    """Ambil riwayat sesi klien (PT, admin, atau klien sendiri)."""
    if request.user.role == 'klien' and request.user.pk != id_klien:
        return _json_error('Akses ditolak.', 403)

    limit = int(request.GET.get('limit', 50))
    sesi_qs = SesiLatihan.objects.filter(
        klien_id=id_klien
    ).select_related('gerakan').order_by('-waktu_mulai')[:limit]

    data = [
        {
            'id_sesi': s.pk,
            'gerakan': s.gerakan.nama_gerakan,
            'waktu_mulai': s.waktu_mulai.strftime('%Y-%m-%d %H:%M'),
            'total_reps': s.total_reps,
            'total_form_error': s.total_form_error,
            'form_error_rate': s.form_error_rate,
            'catatan': s.catatan or '',
        }
        for s in sesi_qs
    ]
    return _json_ok(data)


# ─── GET /api/statistik/<id_klien>/ ─────────────────────────────────────────
@login_required
@require_http_methods(['GET'])
def get_statistik(request, id_klien):
    """Statistik agregat klien untuk PT dashboard."""
    if request.user.role == 'klien' and request.user.pk != id_klien:
        return _json_error('Akses ditolak.', 403)

    qs = SesiLatihan.objects.filter(klien_id=id_klien)
    agg = qs.aggregate(
        total_sesi=Count('pk'),
        total_reps_all=Sum('total_reps'),
        total_error_all=Sum('total_form_error'),
        avg_reps=Avg('total_reps'),
    )

    total_reps = agg['total_reps_all'] or 0
    total_errors = agg['total_error_all'] or 0
    total_combined = total_reps + total_errors
    error_rate = round(total_errors / total_combined * 100, 1) if total_combined > 0 else 0.0

    stats = {
        'total_sesi': agg['total_sesi'] or 0,
        'total_reps_all': total_reps,
        'total_error_all': total_errors,
        'avg_reps': round(float(agg['avg_reps'] or 0), 1),
        'error_rate_pct': error_rate,
    }

    # Data grafik (14 hari terakhir, kronologis)
    grafik_qs = (
        qs.annotate(tanggal=TruncDate('waktu_mulai'))
        .values('tanggal')
        .annotate(reps=Sum('total_reps'), errors=Sum('total_form_error'))
        .order_by('tanggal')
    )[:14]

    grafik = [
        {
            'tanggal': str(g['tanggal']),
            'reps': g['reps'] or 0,
            'errors': g['errors'] or 0,
        }
        for g in grafik_qs
    ]

    return JsonResponse({'status': 'ok', 'statistik': stats, 'grafik': grafik})


# ─── GET /api/gerakan/ ────────────────────────────────────────────────────────
@login_required
@require_http_methods(['GET'])
def get_gerakan(request):
    """Daftar master gerakan untuk frontend JS."""
    data = list(MasterGerakan.objects.values(
        'id', 'nama_gerakan', 'sudut_maksimal', 'wajib_scapular_plane', 'deskripsi'
    ))
    return _json_ok(data)
