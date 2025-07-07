FROM python:3.12

WORKDIR /app

COPY . .

# Install FFMPEG + libx264
RUN apt-get update && \
    apt-get install -y ffmpeg libsm6 libxext6 libgl1
    apt-get clean

RUN pip install --no-cache-dir -r requirements.txt

CMD ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:$PORT"]
