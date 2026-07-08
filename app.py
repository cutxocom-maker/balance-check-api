from flask import Flask, request, jsonify
import subprocess
import os
import re
import shlex

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "service": "Balance Check API",
        "status": "running",
        "endpoints": {
            "check": "POST /check",
            "providers": "GET /providers"
        }
    })

@app.route('/providers')
def providers():
    return jsonify({
        "providers": [
            "blackhawk", "spafinder", "gamestop", 
            "bestbuy", "homedepot", "starbucks"
        ],
        "note": "CAPTCHA providers need ANTI_CAPTCHA_KEY env var"
    })

@app.route('/check', methods=['POST'])
def check():
    data = request.get_json()
    
    if not data or 'provider' not in data or 'card_number' not in data:
        return jsonify({"error": "Need provider and card_number"}), 400
    
    provider = data['provider']
    card = data['card_number']
    
    # Sanitize inputs to prevent command injection
    card = re.sub(r'[^\d]', '', card)  # Keep only digits
    
    # Build command as list (safer)
    cmd = ["balance-check", provider, "-c", card]
    
    if data.get('pin'): 
        pin = re.sub(r'[^\d]', '', str(data['pin']))
        cmd.extend(["-p", pin])
    if data.get('exp_month'): 
        cmd.extend(["-m", str(data['exp_month'])])
    if data.get('exp_year'): 
        cmd.extend(["-y", str(data['exp_year'])])
    if data.get('cvv'): 
        cvv = re.sub(r'[^\d]', '', str(data['cvv']))
        cmd.extend(["-v", cvv])
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=90
        )
        
        output = result.stdout + result.stderr
        
        # Parse balance
        balance_match = re.search(r'\$([\d,]+\.?\d{0,2})', output)
        
        return jsonify({
            "success": result.returncode == 0,
            "provider": provider,
            "card_last_four": card[-4:] if len(card) >= 4 else card,
            "balance": balance_match.group(1).replace(',', '') if balance_match else None,
            "raw_output": output[:1000]
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Request timeout - card check took too long"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
