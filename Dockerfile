# Use official Python slim image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable stdout/stderr unbuffered
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies for Postgres driver
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc libpq-dev \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install Python dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install --upgrade pip \
 && pip install -r requirements.txt \
 && pip install -r requirements-dev.txt

# Copy application code
COPY . .

# Expose the port FastAPI will run on
EXPOSE 8000

# Start the Uvicorn server
CMD ["uvicorn", "fastapi_postgres_app.main:app", "--host", "0.0.0.0", "--port", "8000"]