# Use official Python image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
# We install these directly here so they aren't needed in your local requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir azure-identity azure-keyvault-secrets gunicorn

# Copy project
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "task_manager.wsgi:application"]