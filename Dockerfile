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

# Copy requirements FIRST and install everything
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install balance-check dependencies
RUN pip install --no-cache-dir \
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

# Clone and fix balance-check
RUN git clone https://github.com/stevenmirabito/balance-check.git /tmp/bc && \
    cd /tmp/bc && \
    sed -i 's/dev/1.0.0/g' setup.py && \
    pip install --no-cache-dir . && \
    rm -rf /tmp/bc

# Copy app
COPY app.py .

# Use python -m gunicorn (more reliable)
CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "120", "app:app"]
