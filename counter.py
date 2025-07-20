from deep_sort_realtime.deepsort_tracker import DeepSort
from ultralytics import YOLO
import cv2
import os
import pandas as pd

model = YOLO("yolov8n.pt")  # ganti sesuai model kamu
tracker = DeepSort(max_age=30)  # bisa di-tweak sesuai performa tracking

def process_and_save_video(input_path, output_path):
    vehicle_labels = ['car', 'motorcycle', 'truck', 'bus']
    counted_ids = {label: set() for label in vehicle_labels}
    track_positions = {}

    # Load video
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"[ERROR] Gagal membuka video: {input_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0 or fps is None:
        print("[WARNING] FPS tidak valid, menggunakan default 25")
        fps = 25

    # Pastikan folder output ada
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Lebih aman untuk browser dan OS Linux
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    if not out.isOpened():
        raise RuntimeError(f"[ERROR] Gagal menyimpan video ke: {output_path}")


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

                # Crossing line check
                if track_id not in track_positions:
                    track_positions[track_id] = center_y
                else:
                    prev_y = track_positions[track_id]
                    if (prev_y < count_line_y <= center_y) or (prev_y > count_line_y >= center_y):
                        if track_id not in counted_ids[label]:
                            counted_ids[label].add(track_id)
                    track_positions[track_id] = center_y

                # Draw box and label
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{label} #{track_id}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        # Garis hitung
        cv2.line(frame, (0, count_line_y), (width, count_line_y), (255, 0, 0), 2)

        # Count realtime
        for i, (label, ids) in enumerate(counted_ids.items()):
            cv2.putText(frame, f"{label}: {len(ids)}", (10, 30 + i * 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        out.write(frame)

    cap.release()
    out.release()

    if not os.path.exists(output_path):
        raise RuntimeError(f"[ERROR] File hasil tidak ditemukan: {output_path}")

    # Simpan hasil count ke Excel
    counts = {label: len(ids) for label, ids in counted_ids.items()}
    df = pd.DataFrame(list(counts.items()), columns=["Vehicle", "Count"])

    excel_path = os.path.join("static", "processed", "hasil_perhitungan.xlsx")
    os.makedirs(os.path.dirname(excel_path), exist_ok=True)
    df.to_excel(excel_path, index=False)

    print(f"[INFO] Proses selesai. Kendaraan unik terdeteksi: {counts}")
    print(f"[INFO] Video output: {output_path}")
    print(f"[INFO] Data disimpan ke: {excel_path}")

    return os.path.basename(output_path), os.path.basename(excel_path), counts
