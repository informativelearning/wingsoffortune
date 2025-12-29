# Use the full Python image to ensure all network tools are present
FROM python:3.9

# 1. Create the specific user ID 1000 required by Hugging Face
RUN useradd -m -u 1000 user

# 2. Set the working directory
WORKDIR /app

# 3. Copy requirements and install
COPY --chown=user requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

# 4. Copy the bot code and give the user ownership (Crucial!)
COPY --chown=user bot.py /app/bot.py

# 5. Switch to the user (This turns the internet access back on)
USER user

# 6. Set the path so Python works correctly
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH

# 7. Run the bot
CMD ["python", "bot.py"]