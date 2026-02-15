# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements_dashboard.txt .
RUN pip install --no-cache-dir -r requirements_dashboard.txt

# Copy application files
COPY . .

# Expose port (Cloud Run uses PORT env var, typically 8080)
EXPOSE 8080

# Run streamlit
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
