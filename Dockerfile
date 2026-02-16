FROM python:3.12-slim-bullseye

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies required for PDF processing and rendering
# poppler-utils: for pdfinfo and pdftoppm
# mupdf-tools: for fitz/PyMuPDF optimizations
# libgl1-mesa-glx: required by OpenCV for Vision tasks
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    mupdf-tools \
    unzip \
    zip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create the folder structure defined in blueprint_v2.md
RUN mkdir -p app/api app/core app/db app/models app/services/ai app/services/pdf data/uploads data/processed data/failed

# Copy the application code
COPY . .

# Expose FastAPI's default port
EXPOSE 8000

# Default command to run the app with hot-reloading for development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]