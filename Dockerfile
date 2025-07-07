FROM python:3.12

WORKDIR /app

COPY . .

# Install FFMPEG + libx264
RUN apt-get update && \
    apt-get install -y ffmpeg libsm6 libxext6 libgl1 libx264-dev libavcodec-extra

RUN pip install --no-cache-dir -r requirements.txt

# Create necessary folders
RUN mkdir -p static/uploads static/processed

CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:$PORT"]
