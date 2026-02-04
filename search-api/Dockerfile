# Use Python 3.11 slim image
FROM python:3.11-slim

# Install FFmpeg for clip extraction
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the CLIP model to avoid download during runtime
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('clip-ViT-B-32')"

# Copy application code
COPY cloud_clip_api.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PROJECT_ID=gen-lang-client-0067393875
ENV BUCKET_NAME=gen-lang-client-0067393875-media-1770102442
ENV PORT=8080

# Expose port
EXPOSE 8080

# Run with gunicorn for production
CMD exec gunicorn --bind :$PORT --workers 1 --threads 4 --timeout 300 cloud_clip_api:app
