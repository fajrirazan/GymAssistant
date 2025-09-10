import cv2
import mediapipe as mp
import time
import csv
import tkinter as tk
from PIL import Image, ImageTk

# Inisialisasi MediaPipe
mp_draw = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# Variabel logika
repetisi = 0
set_count = 1
stage = None
last_repetition_time = time.time()
set_timeout = 10
tracking = False  # dikontrol dari tombol

# Fungsi untuk simpan ke CSV
def simpan_ke_csv(repetisi_terakhir, set_terhitung):
    waktu = time.strftime("%Y-%m-%d %H:%M:%S")
    with open('log_latihan.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([waktu, set_terhitung, repetisi_terakhir])

# Inisialisasi kamera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# Fungsi pelacakan frame
def update_frame():
    global repetisi, set_count, stage, last_repetition_time

    ret, frame = cap.read()
    if not ret:
        print("Gagal mengambil frame")
        return

    frame = cv2.flip(frame, 1)
    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)
    current_time = time.time()

    if tracking and results.pose_landmarks:
        landmarks = results.pose_landmarks.landmark

        shoulder_l = [landmarks[11].x * frame.shape[1], landmarks[11].y * frame.shape[0]]
        elbow_l = [landmarks[13].x * frame.shape[1], landmarks[13].y * frame.shape[0]]
        shoulder_r = [landmarks[12].x * frame.shape[1], landmarks[12].y * frame.shape[0]]
        elbow_r = [landmarks[14].x * frame.shape[1], landmarks[14].y * frame.shape[0]]

        # Garis sejajar bahu
        y_bahu = int((shoulder_l[1] + shoulder_r[1]) / 2)
        cv2.line(frame, (0, y_bahu), (frame.shape[1], y_bahu), (0, 255, 255), 2)

        # Toleransi deteksi
        toleransi_y = 35

        if (
            elbow_l[1] > shoulder_l[1] + toleransi_y and
            elbow_r[1] > shoulder_r[1] + toleransi_y
        ):
            stage = "turun"

        if (
            elbow_l[1] <= shoulder_l[1] + toleransi_y and
            elbow_r[1] <= shoulder_r[1] + toleransi_y and
            stage == "turun" and
            abs(elbow_l[0] - shoulder_l[0]) > 40 and
            abs(elbow_r[0] - shoulder_r[0]) > 40
        ):
            repetisi += 1
            stage = "naik"
            last_repetition_time = current_time

        if current_time - last_repetition_time > set_timeout and repetisi > 0:
            set_count += 1
            simpan_ke_csv(repetisi, set_count)
            repetisi = 0
            last_repetition_time = current_time

        mp_draw.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

    # UI Overlay
    cv2.rectangle(frame, (0, 0), (360, 110), (0, 0, 0), -1)
    status_text = "Aktif" if tracking else "Berhenti"
    cv2.putText(frame, f'Repetisi: {repetisi}', (10, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(frame, f'Set     : {set_count}', (10, 75),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(frame, f'Status: {status_text}', (1000, 35),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

    # Konversi frame untuk Tkinter
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    imgtk = ImageTk.PhotoImage(image=img)
    video_label.imgtk = imgtk
    video_label.configure(image=imgtk)

    window.after(10, update_frame)

# Tombol fungsi
def start_tracking():
    global tracking
    tracking = True

def stop_tracking():
    global tracking
    tracking = False

def reset_counter():
    global repetisi, set_count, stage
    repetisi = 0
    set_count = 1
    stage = None

def quit_app():
    cap.release()
    window.destroy()

# GUI Tkinter
window = tk.Tk()
window.title("Penghitung Side Lateral Raise")
window.geometry("1300x800")

video_label = tk.Label(window)
video_label.pack()

control_frame = tk.Frame(window)
control_frame.pack(pady=10)

btn_start = tk.Button(control_frame, text="Start", width=15, command=start_tracking, bg='green', fg='white')
btn_start.grid(row=0, column=0, padx=5)

btn_stop = tk.Button(control_frame, text="Stop", width=15, command=stop_tracking, bg='red', fg='white')
btn_stop.grid(row=0, column=1, padx=5)

btn_reset = tk.Button(control_frame, text="Reset", width=15, command=reset_counter, bg='orange', fg='white')
btn_reset.grid(row=0, column=2, padx=5)

btn_quit = tk.Button(control_frame, text="Keluar", width=15, command=quit_app, bg='gray', fg='white')
btn_quit.grid(row=0, column=3, padx=5)

# Jalankan aplikasi
update_frame()
window.mainloop()