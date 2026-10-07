FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg tesseract-ocr tesseract-ocr-por curl unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Modelo de voz offline (Português)
RUN curl -sL -o /tmp/model.zip https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip \
    && mkdir -p /app/model \
    && unzip -q /tmp/model.zip -d /app/model \
    && cp -r /app/model/vosk-model-small-pt-0.3 /app/model/vosk \
    && rm -rf /tmp/model.zip /app/model/vosk-model-small-pt-0.3

COPY server.py .

EXPOSE 3000
CMD ["python", "server.py"]