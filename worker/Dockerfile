# Use Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies for FFmpeg and OpenCV
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the embedding model to avoid download during runtime
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('clip-ViT-B-32')"

# Copy worker code
COPY ingest_worker.py .
COPY pubsub_listener.py .

# Make scripts executable
RUN chmod +x ingest_worker.py pubsub_listener.py

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PROJECT_ID=gen-lang-client-0067393875
ENV BUCKET_NAME=gen-lang-client-0067393875-media-1770102442

# Default command runs the Pub/Sub listener
CMD ["python", "pubsub_listener.py"]
