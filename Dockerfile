FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Установка зависимостей
RUN apt-get update && \
    apt-get install -y \
    gcc \
    procps \
    net-tools \
    python3-tk \  # Для Tkinter в контейнере
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем только серверный код
COPY server.py .

# Копируем ВСЕ бинарники из локальной папки dist (включая .exe)
COPY dist/ /app/dist/

CMD ["python", "server.py"]