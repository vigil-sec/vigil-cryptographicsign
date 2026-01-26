# Vigil Proof Service
# Authority Surface: Holds private keys, creates signatures
# Local-first deployment

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY trusted_core/ ./trusted_core/
COPY host/ ./host/
COPY main.py .

# Respect PORT environment variable (default: 5000)
ENV PORT=5000
EXPOSE 5000

# Health check
# Note: HEALTHCHECK always uses PORT 5000 from ENV. If you override PORT,
# also set PORT=<your_port> when building or running the image.
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os, requests; port = int(os.getenv('PORT', 5000)); requests.get(f'http://localhost:{port}/health', timeout=5)"

# Run service
CMD ["python", "main.py"]
