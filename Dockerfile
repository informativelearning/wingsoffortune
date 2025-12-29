# Use a lightweight Python version
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Install system tools (needed for some AI libraries)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (to cache them and speed up future builds)
COPY requirements.txt .

# Install Python libraries
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your code (bot.py and knowledge folder)
COPY . .

# THE ENTRY POINT (This tells Zeabur exactly what to run)
CMD ["python", "bot.py"]
