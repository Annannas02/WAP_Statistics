# Use Python official image
FROM python:3.11-slim

# Install required system packages
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    firefox-esr \
    fonts-liberation \
    libnss3 \
    libxss1 \
    libgconf-2-4 \
    libasound2 \
    xauth \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Install geckodriver
RUN wget -q "https://github.com/mozilla/geckodriver/releases/download/v0.36.0/geckodriver-v0.36.0-linux64.tar.gz" \
    && tar -xvzf geckodriver-v0.36.0-linux64.tar.gz \
    && mv geckodriver /usr/local/bin/ \
    && chmod +x /usr/local/bin/geckodriver \
    && rm geckodriver-v0.36.0-linux64.tar.gz

# Set environment variables
ENV MOZ_HEADLESS=1

# Set working directory
WORKDIR /app

# Copy all project files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Flask default port
EXPOSE 5000

# Run the app
CMD ["python", "main.py"]
