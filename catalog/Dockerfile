FROM python:3.11-slim

# Install system dependencies including lxml for sitemap parsing
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-por \
    libpq-dev \
    gcc \
    curl \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for sitemap processing
RUN pip install --no-cache-dir \
    httpx \
    beautifulsoup4 \
    lxml

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
