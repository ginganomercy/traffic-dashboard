from deep_sort_realtime.deepsort_tracker import DeepSort
from ultralytics import YOLO
import cv2
import os
import pandas as pd

model = YOLO("yolov8n.pt")  # Gunakan model yang ringan untuk performa cepat
tracker = DeepSort(max_age=30)

def process_and_save_video(input_path, output_path):
    vehicle_labels = ['car', 'motorcycle', 'truck', 'bus']
    counted_ids = {label: set() for label in vehicle_labels}
    track_positions = {}

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"[ERROR] Gagal membuka video: {input_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or fps is None:
        print("[WARNING] FPS tidak valid, fallback ke 25")
        fps = 25

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    if not out.isOpened():
        raise RuntimeError(f"[ERROR] Tidak bisa membuka VideoWriter ke: {output_path}")

    print(f"[INFO] Mulai proses video: {input_path}")
    print(f"[INFO] Output akan disimpan ke: {output_path}")

    count_line_y = int(height * 0.6)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        results = model.predict(frame, conf=0.3)[0]
        detections = []

        for box in results.boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id]
            if label in vehicle_labels:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = float(box.conf[0])
                detections.append(([x1, y1, x2 - x1, y2 - y1], confidence, label))

        tracks = tracker.update_tracks(detections, frame=frame)

        for track in tracks:
            if not track.is_confirmed():
                continue

            track_id = track.track_id
            ltrb = track.to_ltrb()
            x1, y1, x2, y2 = map(int, ltrb)
            label = track.get_det_class()

            if label in vehicle_labels:
                center_y = int((y1 + y2) / 2)
                if track_id not in track_positions:
                    track_positions[track_id] = center_y
                else:
                    prev_y = track_positions[track_id]
                    if (prev_y < count_line_y <= center_y) or (prev_y > count_line_y >= center_y):
                        if track_id not in counted_ids[label]:
                            counted_ids[label].add(track_id)
                    track_positions[track_id] = center_y

                # Gambar bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{label} #{track_id}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Gambar garis crossing
        cv2.line(frame, (0, count_line_y), (width, count_line_y), (255, 0, 0), 2)

        # Info jumlah kendaraan realtime
        for i, (label, ids) in enumerate(counted_ids.items()):
            cv2.putText(frame, f"{label}: {len(ids)}", (10, 30 + i * 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        out.write(frame)

    cap.release()
    out.release()

    # Cek ukuran file hasil
    print("[DEBUG] Ukuran video hasil:", os.path.getsize(output_path))

    if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
        raise RuntimeError(f"[ERROR] File hasil tidak valid atau kosong: {output_path}")

    # Simpan hasil perhitungan ke Excel
    counts = {label: len(ids) for label, ids in counted_ids.items()}
    df = pd.DataFrame(list(counts.items()), columns=["Vehicle", "Count"])

    excel_path = os.path.join("static", "processed", "hasil_perhitungan.xlsx")
    os.makedirs(os.path.dirname(excel_path), exist_ok=True)
    df.to_excel(excel_path, index=False)

    print(f"[INFO] Selesai. Jumlah kendaraan: {counts}")
    print(f"[INFO] Video disimpan di: {output_path}")
    print(f"[INFO] Excel disimpan di: {excel_path}")

    return os.path.basename(output_path), os.path.basename(excel_path), counts
