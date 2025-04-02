FROM python:3.10-slim

# Указываем явный порт для приложения
ENV PORT=8765

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    procps \  \
    net-tools \ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

# Используем переменную окружения для порта
CMD ["sh", "-c", "python server.py --port ${PORT}"]