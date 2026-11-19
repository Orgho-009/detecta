FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV DETECTA_DESKTOP=0

WORKDIR /app

# OpenCV and FFmpeg runtime libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip

# Try CUDA 12.1 wheel first, fall back to default PyPI build
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cu121 || \
    pip install --no-cache-dir torch torchvision

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "run_dashboard.py", "--no-browser"]
