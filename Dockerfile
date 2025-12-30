FROM python:3.9-slim

LABEL "language"="python"

WORKDIR /app

COPY requirements.txt .

# FIX: Install libgomp1 (Required for FAISS/FastEmbed to run)
# We keep build-essential for the install step, then remove it, but we KEEP libgomp1
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential libgomp1 && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y --auto-remove build-essential && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

COPY . .

CMD ["python", "bot.py"]
