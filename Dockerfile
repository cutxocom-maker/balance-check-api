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

# Copy requirements FIRST
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

# Clone and fix balance-check (PYTHON METHOD - 100% works)
RUN git clone https://github.com/stevenmirabito/balance-check.git /tmp/bc && \
    cd /tmp/bc && \
    python3 << 'EOF'
import re
with open('setup.py', 'r') as f:
    content = f.read()
print("BEFORE:", [line for line in content.split('\n') if 'version' in line.lower()])
content = re.sub(r"version\s*=\s*['\"]dev['\"]", "version='1.0.0'", content)
with open('setup.py', 'w') as f:
    f.write(content)
print("AFTER:", [line for line in content.split('\n') if 'version' in line.lower()])
EOF
RUN cd /tmp/bc && pip install --no-cache-dir . && rm -rf /tmp/bc

# Copy app
COPY app.py .

CMD ["python", "-m", "gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "120", "app:app"]
