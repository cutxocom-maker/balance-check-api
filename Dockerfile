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

# Install dependencies first
RUN pip install \
    selenium==4.15.2 \
    requests==2.31.0 \
    beautifulsoup4==4.12.2 \
    lxml==4.9.3 \
    webdriver-manager==4.0.1 \
    cerberus==1.3.4 \
    colorama==0.4.6 \
    tqdm==4.66.1 \
    python-anticaptcha==1.0.0 \
    Pillow==10.1.0

# Clone and fix balance-check (BULLETPROOF METHOD)
RUN git clone https://github.com/stevenmirabito/balance-check.git /tmp/bc && \
    cd /tmp/bc
