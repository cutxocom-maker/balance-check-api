from flask import Flask, request, jsonify
import subprocess
import os
import re

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
    
    # Build command - balance-check expects: provider card_number [options]
    cmd = ["balance-check", provider, card]
    
    # Build options string
    options = []
    if data.get('pin'): 
        options.extend(["-p", str(data['pin'])])
    if data.get('exp_month'): 
        options.extend(["-m", str(data['exp_month'])])
    if data.get('exp_year'): 
        options.extend(["-y", str(data['exp_year'])])
    if data.get('cvv'): 
        options.extend(["-v", str(data['cvv'])])
    
    cmd.extend(options)
    
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=90
        )
        
        output = result.stdout + result.stderr
        
        # Parse balance from output
        balance_match = re.search(r'Balance[:\s]*\$?([\d,]+\.?\d{0,2})', output, re.IGNORECASE)
        
        return jsonify({
            "success": result.returncode == 0,
            "provider": provider,
            "card_last_four": card[-4:] if len(card) >= 4 else card,
            "balance": float(balance_match.group(1).replace(',', '')) if balance_match else None,
            "raw_output": output[:2000]
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Request timeout"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
