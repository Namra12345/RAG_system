# Use the official Python 3.13 slim image
FROM python:3.13-slim

# Set working directory inside the container
WORKDIR /app

# Set environment variables to keep Python clean and responsive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install essential system build dependencies 
# (Required for ONNX runtime / fastembed dependencies on some Linux builds)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY ./app ./app

# Expose the internal container port FastAPI listens to
EXPOSE 8000

# Start Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]