/**
 * SmartGym AI — pose_engine.js
 * Wrapper MediaPipe Tasks Vision untuk deteksi pose real-time via webcam.
 * Pengganti pose_detector.py (Python/OpenCV) → JavaScript/WebAssembly
 *
 * API: MediaPipe Tasks Vision (package terbaru, bukan MediaPipe legacy)
 * CDN: https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision
 */

'use strict';

class PoseEngine {
    constructor() {
        this.poseLandmarker = null;
        this.isReady = false;
        this.lastResults = null;
        this._runningMode = 'VIDEO';
        this._lastVideoTime = -1;
    }

    // ─── INISIALISASI ─────────────────────────────────────────────────────────
    /**
     * Memuat model MediaPipe Pose Landmarker dari CDN.
     * Harus dipanggil sekali sebelum detect().
     */
    async init() {
        const { PoseLandmarker, FilesetResolver } = await import(
            'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/vision_bundle.mjs'
        );

        const vision = await FilesetResolver.forVisionTasks(
            'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm'
        );

        this.poseLandmarker = await PoseLandmarker.createFromOptions(vision, {
            baseOptions: {
                modelAssetPath: 'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task',
                delegate: 'GPU',
            },
            runningMode: this._runningMode,
            numPoses: 1,
            minPoseDetectionConfidence: 0.5,
            minPosePresenceConfidence: 0.5,
            minTrackingConfidence: 0.5,
        });

        this.isReady = true;
        console.log('[PoseEngine] MediaPipe Pose Landmarker siap.');
        return this;
    }

    // ─── DETEKSI POSE ─────────────────────────────────────────────────────────
    /**
     * Mendeteksi pose dari video element saat ini.
     * @param {HTMLVideoElement} videoEl
     * @returns {Object|null} Hasil landmark atau null
     */
    detectFromVideo(videoEl) {
        if (!this.isReady || !videoEl) return null;

        const nowMs = performance.now();
        if (videoEl.currentTime === this._lastVideoTime) return this.lastResults;

        this._lastVideoTime = videoEl.currentTime;
        this.lastResults = this.poseLandmarker.detectForVideo(videoEl, nowMs);
        return this.lastResults;
    }

    // ─── AMBIL LANDMARK ───────────────────────────────────────────────────────
    /**
     * Mengambil koordinat landmark berdasarkan nama (dari LANDMARK_IDX di biomechanics.js).
     * Mengembalikan koordinat normalisasi {x, y, z} (0.0 – 1.0)
     *
     * @param {string} nama - Nama landmark (contoh: 'BAHU_KIRI')
     * @param {Object} [results] - Hasil detect (opsional, pakai lastResults jika kosong)
     * @returns {{x: number, y: number, z: number}|null}
     */
    getLandmark(nama, results = null) {
        const res = results || this.lastResults;
        if (!res || !res.landmarks || res.landmarks.length === 0) return null;

        const idx = window.Biomechanics.LANDMARK_IDX[nama.toUpperCase()];
        if (idx === undefined) return null;

        const lm = res.landmarks[0][idx];
        if (!lm) return null;
        return { x: lm.x, y: lm.y, z: lm.z, visibility: lm.visibility };
    }

    /**
     * Mengambil beberapa landmark sekaligus.
     * @param {string[]} names
     * @returns {Object} {NAMA: {x,y,z}|null, ...}
     */
    getLandmarks(names) {
        const result = {};
        for (const name of names) {
            result[name] = this.getLandmark(name);
        }
        return result;
    }

    // ─── CEK POSE TERDETEKSI ─────────────────────────────────────────────────
    poseDetected() {
        return (
            this.lastResults !== null &&
            this.lastResults.landmarks &&
            this.lastResults.landmarks.length > 0
        );
    }

    // ─── GAMBAR SKELETON ─────────────────────────────────────────────────────
    /**
     * Menggambar skeleton & landmark di canvas overlay.
     * @param {CanvasRenderingContext2D} ctx - Context canvas
     * @param {number} width - Lebar canvas
     * @param {number} height - Tinggi canvas
     * @param {Object} [results] - Hasil detect
     */
    drawSkeleton(ctx, width, height, results = null) {
        const res = results || this.lastResults;
        if (!res || !res.landmarks || res.landmarks.length === 0) return;

        const landmarks = res.landmarks[0];
        const connections = window.PoseLandmarkerConnections || [];

        ctx.clearRect(0, 0, width, height);

        // Gambar koneksi (tulang)
        ctx.strokeStyle = '#00B4D8';
        ctx.lineWidth = 2;
        for (const [start, end] of connections) {
            const s = landmarks[start];
            const e = landmarks[end];
            if (!s || !e) continue;
            ctx.beginPath();
            ctx.moveTo(s.x * width, s.y * height);
            ctx.lineTo(e.x * width, e.y * height);
            ctx.stroke();
        }

        // Gambar landmark (titik sendi)
        for (const lm of landmarks) {
            ctx.beginPath();
            ctx.arc(lm.x * width, lm.y * height, 5, 0, 2 * Math.PI);
            ctx.fillStyle = '#00E4B0';
            ctx.fill();
        }
    }

    // ─── KONVERSI KE PIXEL ────────────────────────────────────────────────────
    /**
     * Mengkonversi koordinat normalisasi ke pixel berdasarkan dimensi canvas.
     */
    toPixel(lm, width, height) {
        if (!lm) return null;
        return { x: lm.x * width, y: lm.y * height, z: lm.z };
    }
}

// Koneksi untuk gambar skeleton (sesuai MediaPipe Pose topology)
window.PoseLandmarkerConnections = [
    [11, 12], [11, 13], [13, 15], [12, 14], [14, 16], // Tubuh atas
    [11, 23], [12, 24], [23, 24],                       // Badan
    [23, 25], [25, 27], [24, 26], [26, 28],             // Kaki
    [0, 1],  [1, 2],   [2, 3],   [3, 7],               // Wajah kiri
    [0, 4],  [4, 5],   [5, 6],   [6, 8],               // Wajah kanan
];

window.PoseEngine = PoseEngine;
