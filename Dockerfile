# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Create uploads directories for persistent storage
RUN mkdir -p /app/uploads/avatars /app/uploads/voice

# Copy project files
COPY . /app/

# Expose port
EXPOSE 8000

# Start Gunicorn server (production WSGI server for Flask)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "app:app"]
