from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "service": "Balance Check API",
        "usage": "POST /check with JSON body",
        "example": {
            "provider": "blackhawk",
            "card_number": "4111111111111111",
            "exp_month": "12",
            "exp_year": "24",
            "cvv": "999"
        }
    })

@app.route('/providers')
def providers():
    """List supported providers"""
    return jsonify({
        "providers": [
            "blackhawk", "spafinder", "gamestop", 
            "bestbuy", "homedepot", "starbucks"
        ],
        "note": "CAPTCHA providers need ANTI_CAPTCHA_KEY env var"
    })

@app.route('/check', methods=['POST'])
def check():
    """Check card balance"""
    data = request.get_json()
    
    if not data or 'provider' not in data or 'card_number' not in data:
        return jsonify({"error": "Need provider and card_number"}), 400
    
    provider = data['provider']
    card = data['card_number']
    
    # Build command
    cmd = ["balance-check", provider, "-c", card]
    
    # Add optional fields
    if data.get('pin'): 
        cmd.extend(["-p", data['pin']])
    if data.get('exp_month'): 
        cmd.extend(["-m", data['exp_month']])
    if data.get('exp_year'): 
        cmd.extend(["-y", data['exp_year']])
    if data.get('cvv'): 
        cmd.extend(["-v", data['cvv']])
    
    # Run balance-check CLI
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=90,
            env={**os.environ, 'PYTHONUNBUFFERED': '1'}
        )
        
        output = result.stdout or result.stderr
        
        # Parse balance from output
        import re
        balance_match = re.search(r'\$([\d,]+\.?\d{0,2})', output)
        
        return jsonify({
            "success": result.returncode == 0,
            "provider": provider,
            "card_last_four": card[-4:],
            "balance": balance_match.group(1).replace(',', '') if balance_match else None,
            "output": output[:500]  # limit output
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Timeout - card check took too long"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
