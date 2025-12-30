FROM python:3.9-slim

LABEL "language"="python"

WORKDIR /app

COPY requirements.txt .

# Your optimized install step (Excellent work here)
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y --auto-remove build-essential && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY . .

# DELETED: EXPOSE 8080 (Prevents Zeabur from killing the bot for failing health checks)

CMD ["python", "bot.py"]
