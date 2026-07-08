from flask import Flask, request, jsonify
import subprocess
import os
import re
import tempfile
import csv

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
    card = str(data['card_number']).strip()
    
    # Create temp CSV file (balance-check expects CSV input)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        writer = csv.writer(f)
        
        # Determine CSV headers based on provider
        if data.get('exp_month'):  # Prepaid card
            writer.writerow(['card_number', 'exp_month', 'exp_year', 'cvv'])
            writer.writerow([
                card,
                data.get('exp_month', ''),
                data.get('exp_year', ''),
                data.get('cvv', '')
            ])
        else:  # Gift card with PIN
            writer.writerow(['card_number', 'pin'])
            writer.writerow([
                card,
                data.get('pin', '')
            ])
        temp_file = f.name
    
    try:
        # Run balance-check with CSV file
        cmd = ["balance-check", provider, temp_file]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        output = result.stdout + result.stderr
        
        # Parse balance from output
        balance_match = re.search(r'Balance[:\s]*\$?([\d,]+\.?\d{0,2})', output, re.IGNORECASE)
        
        return jsonify({
            "success": result.returncode == 0,
            "provider": provider,
            "card_last_four": card[-4:] if len(card) >= 4 else card,
            "balance": float(balance_match.group(1).replace(',', '')) if balance_match else None,
            "raw_output": output[:3000]
        })
        
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Request timeout"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_file)
        except:
            pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
