FROM python:3.10-slim

ENV PORT=8765

WORKDIR /app

# Установка зависимостей
RUN apt-get update && \
    apt-get install -y \
    gcc \
    procps \
    net-tools && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

CMD ["sh", "-c", "python server.py --port ${PORT}"]