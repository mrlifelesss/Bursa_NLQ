# ---- Build a small, production-ready image
FROM python:3.12-slim

# Avoid writing .pyc, ensure unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install deps first (better layer caching)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# App Runner (and our local run) will hit port 8080
EXPOSE 8080

# Start the server (bind to 0.0.0.0 so Docker can forward)
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8080"]
