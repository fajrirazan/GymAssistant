"""
Management command: python manage.py seed_data
Mengisi data awal: akun Admin, master gerakan Side Lateral Raise
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from sesi.models import MasterGerakan

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed data awal: akun admin default + master gerakan'

    def handle(self, *args, **options):
        self.stdout.write(self.style.HTTP_INFO('\n[Seed] Memeriksa data awal...\n'))

        # ── Akun Admin ────────────────────────────────────────────────────────
        if not User.objects.filter(role='admin').exists():
            User.objects.create_superuser(
                username='admin',
                password='admin123',
                role='admin',
                email='admin@smartgymai.com'
            )
            self.stdout.write(self.style.SUCCESS(
                '[OK] Akun Admin dibuat -> username: admin | password: admin123'
            ))
        else:
            self.stdout.write('  [INFO] Akun Admin sudah ada.')

        # ── Master Gerakan: Side Lateral Raise ────────────────────────────────
        gerakan, created = MasterGerakan.objects.get_or_create(
            nama_gerakan='Side Lateral Raise',
            defaults={
                'sudut_maksimal': 90.00,
                'wajib_scapular_plane': True,
                'deskripsi': (
                    'Gerakan elevasi lateral bahu. Batas aman 90° (dari jurnal medis). '
                    'Wajib pada Scapular Plane (condong 30° ke depan) untuk '
                    'mencegah shoulder impingement.'
                ),
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(
                '  [OK] Master Gerakan: Side Lateral Raise (sudut maks=90°, Scapular Plane=Ya)'
            ))
        else:
            self.stdout.write('  [INFO] Master Gerakan Side Lateral Raise sudah ada.')

        self.stdout.write(self.style.SUCCESS('\n[✓] Seed data selesai!\n'))
