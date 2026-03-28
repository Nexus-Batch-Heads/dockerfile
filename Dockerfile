# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ACCEPT_EULA=Y

# Set work directory
WORKDIR /app

# Install system dependencies and Microsoft ODBC Driver 17 for SQL Server
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    apt-transport-https \
    gnupg2 \
    unixodbc-dev \
    gcc \
    g++ \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends msodbcsql17 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

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
