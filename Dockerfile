FROM python:3.11-slim

# Install Chrome + dependencies
RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl \
    chromium chromium-driver \
    git \
    && rm -rf /var/lib/apt/lists/*

ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

WORKDIR /app

# Install balance-check from GitHub
RUN pip install git+https://github.com/stevenmirabito/balance-check.git

# Install Flask
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "120", "app:app"]
