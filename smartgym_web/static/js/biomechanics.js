/**
 * SmartGym AI — biomechanics.js
 * Port dari app/ai_engine/biomechanics.py ke JavaScript
 * Logika kalkulasi sudut sendi & validasi form Side Lateral Raise
 */

'use strict';

// ─── KONSTANTA BIOMEKANIKA (dari Jurnal Medis) ───────────────────────────────
const SUDUT_AMAN_MAKS  = 90.0;   // Batas maksimal elevasi (°) — Shoulder Impingement
const TOLERANSI_SUDUT  = 5.0;    // Toleransi ±5°
const SCAPULAR_Z_THRESHOLD = 0.02; // Threshold depth Z untuk Scapular Plane

// Index landmark MediaPipe Pose (33 titik sendi)
const LANDMARK_IDX = {
    HIDUNG:             0,
    BAHU_KIRI:         11,
    BAHU_KANAN:        12,
    SIKU_KIRI:         13,
    SIKU_KANAN:        14,
    PERGELANGAN_KIRI:  15,
    PERGELANGAN_KANAN: 16,
    PINGGUL_KIRI:      23,
    PINGGUL_KANAN:     24,
};

// ─── FUNGSI 1: HITUNG SUDUT SENDI ─────────────────────────────────────────────
/**
 * Menghitung sudut (derajat) yang terbentuk oleh 3 titik koordinat.
 * Port dari hitung_sudut() Python/NumPy menggunakan arctan2.
 *
 * @param {Object} a - Titik pertama {x, y} — Pinggul
 * @param {Object} b - Titik tengah  {x, y} — Bahu (vertex)
 * @param {Object} c - Titik ketiga  {x, y} — Siku
 * @returns {number} Sudut dalam derajat (0–180)
 */
function hitungSudut(a, b, c) {
    const radians = Math.atan2(c.y - b.y, c.x - b.x)
                  - Math.atan2(a.y - b.y, a.x - b.x);
    let sudut = Math.abs(radians * (180 / Math.PI));
    if (sudut > 180.0) sudut = 360.0 - sudut;
    return Math.round(sudut * 100) / 100;
}

// ─── FUNGSI 2: KLASIFIKASI STAGE (NAIK/TURUN) ────────────────────────────────
/**
 * Menentukan apakah lengan naik/turun dan apakah rep baru terhitung.
 * Port dari klasifikasi_stage() Python.
 *
 * @param {number} sudutElevasi - Sudut elevasi bahu saat ini
 * @param {string} stageSaatIni - Stage sebelumnya ('naik'|'turun'|null)
 * @param {number} [sudutNaik=75] - Threshold sudut "naik"
 * @param {number} [sudutTurun=30] - Threshold sudut "turun"
 * @returns {{stage: string, repTerhitung: boolean}}
 */
function klasifikasiStage(sudutElevasi, stageSaatIni, sudutNaik = 75, sudutTurun = 30) {
    let stage = stageSaatIni;
    let repTerhitung = false;

    if (sudutElevasi <= sudutTurun) {
        stage = 'turun';
    } else if (sudutElevasi >= sudutNaik && stageSaatIni === 'turun') {
        stage = 'naik';
        repTerhitung = true;
    }
    return { stage, repTerhitung };
}

// ─── FUNGSI 3: VALIDASI FORM LATERAL RAISE ────────────────────────────────────
/**
 * Memvalidasi form Side Lateral Raise sesuai parameter biomekanika jurnal.
 * Port dari validasi_lateral_raise() Python.
 *
 * @param {number} sudutElevasi  - Sudut elevasi bahu (dari hitungSudut)
 * @param {number} [bahuZ=0]     - Koordinat Z bahu (depth MediaPipe)
 * @param {number} [pergelanganZ=0] - Koordinat Z pergelangan
 * @param {boolean} [cekScapular=true] - Toggle validasi Scapular Plane
 * @returns {{valid: boolean, kode: string, pesan: string}}
 */
function validasiLateralRaise(sudutElevasi, bahuZ = 0, pergelanganZ = 0, cekScapular = true) {
    // Validasi 1: Batas Elevasi 90° (Shoulder Impingement Risk)
    if (sudutElevasi > SUDUT_AMAN_MAKS + TOLERANSI_SUDUT) {
        return {
            valid: false,
            kode: 'ELEV_LEBIH',
            pesan: `⚠ ELEVASI BERLEBIHAN: Lengan melewati bahu (>${SUDUT_AMAN_MAKS}°)! Risiko shoulder impingement.`,
        };
    }

    // Validasi 2: Scapular Plane (Z-axis depth)
    if (cekScapular && bahuZ !== 0 && pergelanganZ > bahuZ + SCAPULAR_Z_THRESHOLD) {
        return {
            valid: false,
            kode: 'SCAPULAR',
            pesan: '⚠ FORM ERROR: Lengan terlalu sejajar badan. Condongkan ke depan 30° (Scapular Plane)!',
        };
    }

    return { valid: true, kode: 'OK', pesan: '✓ Form Aman' };
}

// ─── FUNGSI UTILITAS ─────────────────────────────────────────────────────────

/**
 * Mengembalikan warna HEX berdasarkan sudut elevasi.
 * Hijau=aman, Kuning=mendekati batas, Merah=melampaui batas.
 * @param {number} sudut
 * @returns {string} Warna HEX
 */
function getWarnaSudut(sudut) {
    if (sudut < 70)  return '#3FB950'; // Hijau aman
    if (sudut < 88)  return '#E3B341'; // Kuning peringatan
    return '#F85149';                  // Merah bahaya
}

/**
 * Versi singkat pesan untuk overlay HUD.
 * @param {string} kode
 * @returns {string}
 */
function formatPesanWarning(kode) {
    const map = {
        'ELEV_LEBIH': 'TURUNKAN LENGAN! >90°',
        'SCAPULAR':   'CONDONG KE DEPAN 30°',
        'OK':         '',
    };
    return map[kode] || '';
}

// Export untuk dipakai modul lain
window.Biomechanics = {
    LANDMARK_IDX,
    SUDUT_AMAN_MAKS,
    hitungSudut,
    klasifikasiStage,
    validasiLateralRaise,
    getWarnaSudut,
    formatPesanWarning,
};
