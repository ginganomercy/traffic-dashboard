FROM python:3.12

WORKDIR /app

COPY . .

# Install FFMPEG + dependencies
RUN apt-get update && \
    apt-get install -y ffmpeg libsm6 libxext6 libgl1

# Buat folder agar tidak error saat runtime
RUN mkdir -p static/uploads static/processed

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Gunakan port 5000 default jika $PORT tidak diset (saat di-local)
ENV PORT=5000

# Jalankan server Gunicorn
CMD gunicorn app:app --workers 1 --timeout 600 --bind 0.0.0.0:$PORT
