/**
 * SmartGym AI — session_manager.js
 * Mengelola sesi latihan: rep counter, form error counter, timer,
 * dan pengiriman data ke Django REST API saat sesi berakhir.
 */

'use strict';

class SessionManager {
    constructor({ gerakanId, userId, csrfToken, onUpdate }) {
        this.gerakanId = gerakanId;
        this.userId = userId;
        this.csrfToken = csrfToken;
        this.onUpdate = onUpdate || (() => {});

        // State sesi
        this.totalReps = 0;
        this.totalErrors = 0;
        this.stage = null;          // 'naik' | 'turun' | null
        this.isActive = false;
        this.startTime = null;
        this.elapsedSeconds = 0;
        this._timerInterval = null;

        // State audio feedback
        this._lastWarningTime = 0;
        this._warningCooldownMs = 2000;
    }

    // ─── KONTROL SESI ─────────────────────────────────────────────────────────

    mulai() {
        this.totalReps = 0;
        this.totalErrors = 0;
        this.stage = null;
        this.isActive = true;
        this.startTime = Date.now();
        this.elapsedSeconds = 0;

        this._timerInterval = setInterval(() => {
            this.elapsedSeconds = Math.floor((Date.now() - this.startTime) / 1000);
            this.onUpdate(this._buildState());
        }, 1000);

        this.onUpdate(this._buildState());
        console.log('[SessionManager] Sesi dimulai.');
    }

    async akhiri() {
        if (!this.isActive) return null;

        this.isActive = false;
        clearInterval(this._timerInterval);

        const state = this._buildState();
        this.onUpdate(state);

        const result = await this._kirimKeDjango();
        console.log('[SessionManager] Sesi diakhiri. Reps:', this.totalReps, 'Errors:', this.totalErrors);
        return result;
    }

    reset() {
        this.isActive = false;
        clearInterval(this._timerInterval);
        this.totalReps = 0;
        this.totalErrors = 0;
        this.stage = null;
        this.elapsedSeconds = 0;
        this.onUpdate(this._buildState());
    }

    // ─── PROSES FRAME AI ──────────────────────────────────────────────────────

    /**
     * Dipanggil setiap frame oleh loop AI.
     * Menerima landmark dari PoseEngine dan menjalankan logika biomekanik.
     *
     * @param {Object} landmarks - { PINGGUL_KIRI, BAHU_KIRI, SIKU_KIRI, PERGELANGAN_KIRI, ... }
     * @param {string} side - 'KIRI' atau 'KANAN'
     * @returns {Object} { sudut, hasil, state }
     */
    prosesFrame(landmarks, side = 'KIRI') {
        if (!this.isActive) return null;

        const BIO = window.Biomechanics;

        const pinggul     = landmarks[`PINGGUL_${side}`];
        const bahu        = landmarks[`BAHU_${side}`];
        const siku        = landmarks[`SIKU_${side}`];
        const pergelangan = landmarks[`PERGELANGAN_${side}`];

        if (!pinggul || !bahu || !siku || !pergelangan) {
            return { sudut: null, hasil: null, state: this._buildState() };
        }

        // 1. Hitung sudut elevasi
        const sudut = BIO.hitungSudut(pinggul, bahu, siku);

        // 2. Klasifikasi stage & hitung rep
        const { stage, repTerhitung } = BIO.klasifikasiStage(sudut, this.stage);
        this.stage = stage;
        if (repTerhitung) this.totalReps++;

        // 3. Validasi form (hanya saat lengan terangkat)
        const hasil = BIO.validasiLateralRaise(sudut, bahu.z, pergelangan.z, true);
        if (!hasil.valid && repTerhitung === false) {
            const now = Date.now();
            if (now - this._lastWarningTime > this._warningCooldownMs) {
                this.totalErrors++;
                this._lastWarningTime = now;
            }
        }

        const state = this._buildState(sudut, hasil);
        this.onUpdate(state);
        return { sudut, hasil, state };
    }

    // ─── KIRIM DATA KE DJANGO ─────────────────────────────────────────────────

    async _kirimKeDjango() {
        const payload = {
            gerakan_id: this.gerakanId,
            reps: this.totalReps,
            errors: this.totalErrors,
            catatan: `Durasi: ${this._formatWaktu(this.elapsedSeconds)}`,
        };

        try {
            const response = await fetch('/api/simpan-sesi/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.csrfToken,
                },
                body: JSON.stringify(payload),
            });

            const data = await response.json();
            if (response.ok && data.status === 'ok') {
                console.log('[SessionManager] Data sesi terkirim ke server:', data);
                return { sukses: true, data };
            } else {
                console.error('[SessionManager] Gagal kirim sesi:', data);
                return { sukses: false, error: data.pesan };
            }
        } catch (err) {
            console.error('[SessionManager] Network error:', err);
            return { sukses: false, error: err.message };
        }
    }

    // ─── HELPERS ─────────────────────────────────────────────────────────────

    _buildState(sudut = null, hasil = null) {
        return {
            isActive: this.isActive,
            totalReps: this.totalReps,
            totalErrors: this.totalErrors,
            stage: this.stage,
            elapsedSeconds: this.elapsedSeconds,
            elapsedFormatted: this._formatWaktu(this.elapsedSeconds),
            sudut,
            hasil,
            errorRate: this.totalReps + this.totalErrors > 0
                ? Math.round(this.totalErrors / (this.totalReps + this.totalErrors) * 100)
                : 0,
        };
    }

    _formatWaktu(detik) {
        const m = Math.floor(detik / 60).toString().padStart(2, '0');
        const s = (detik % 60).toString().padStart(2, '0');
        return `${m}:${s}`;
    }
}

window.SessionManager = SessionManager;

// ─── HELPER CSRF TOKEN ────────────────────────────────────────────────────────
/**
 * Mengambil nilai CSRF token dari cookie Django.
 * Dipakai di header X-CSRFToken setiap request POST.
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let c of cookies) {
            c = c.trim();
            if (c.startsWith(name + '=')) {
                cookieValue = decodeURIComponent(c.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

window.getCookie = getCookie;
