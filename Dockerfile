FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Установка всех зависимостей для Tkinter
RUN apt-get update && \
    apt-get install -y \
    gcc \
    procps \
    net-tools \
    python3-tk \
    tk \
    tcl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .
COPY dist/ /app/dist/

CMD ["python", "server.py"]