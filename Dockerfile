# Gunakan Python image resmi
FROM python:3.12-slim

# Set direktori kerja dalam container
WORKDIR /app

# Salin semua file dari project ke dalam container
COPY . .

# Install dependensi OS yang dibutuhkan untuk OpenCV & ffmpeg
RUN apt-get update && \
    apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    libx264-dev \
    libavcodec-extra \
    && rm -rf /var/lib/apt/lists/*

# Buat folder agar tidak error saat runtime
RUN mkdir -p static/uploads static/processed

# Install dependensi Python dari requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Jalankan aplikasi menggunakan gunicorn
CMD ["gunicorn", "app:app", "--workers=1", "--worker-class=gevent", "--timeout=600", "--bind=0.0.0.0:$PORT"]
