# Detecta AI Surveillance System — Production Container
FROM python:3.10-slim

# Prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV DETECTA_DESKTOP=0

WORKDIR /app

# Install system dependencies for OpenCV, FFmpeg, and build essentials
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install PyTorch (with CUDA support if GPU runtime is attached)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cu121 || \
    pip install --no-cache-dir torch torchvision

# Copy requirements and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose web dashboard port
EXPOSE 8000

# Start Detecta web dashboard backend in headless container mode
CMD ["python", "run_dashboard.py", "--no-browser"]
