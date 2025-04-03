FROM python:3.10-slim

# Устанавливаем переменные окружения
ENV PORT=8765
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && \
    apt-get install -y \
    gcc \
    procps \
    net-tools && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Копируем файлы приложения
COPY requirements.txt .
COPY server.py .
COPY dist/ClickControlApp.exe .
COPY ClickControlApp .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt aiohttp

# Запуск сервера
CMD ["python", "server.py"]