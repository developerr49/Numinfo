from flask import Flask, request, jsonify, render_template_string, redirect, url_for
import requests
from bs4 import BeautifulSoup
import os
import random

app = Flask(__name__)

# In-memory database for API Keys (Free limit 10, Paid unlimited)
API_KEYS_DB = {
    "rahul748": {"tier": "free", "requests_left": 10},
    "rahul999": {"tier": "paid", "requests_left": 999999}
}

# Embedded Admin Panel HTML
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rahul API Admin Panel</title>
    <style>
        body { font-family: Arial, sans-serif; background: #0f172a; color: #f8fafc; padding: 20px; }
        .container { max-width: 600px; margin: auto; background: #1e293b; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
        h2 { color: #38bdf8; text-align: center; }
        .btn { background: #0284c7; color: white; border: none; padding: 10px 15px; cursor: pointer; border-radius: 5px; font-weight: bold; width: 100%; margin-top: 10px; }
        .btn:hover { background: #0ea5e9; }
        .btn-danger { background: #dc2626; padding: 5px 10px; width: auto; }
        .btn-danger:hover { background: #ef4444; }
        table { width: 100%; margin-top: 20px; border-collapse: collapse; }
        th, td { padding: 10px; border-bottom: 1px solid #334155; text-align: left; font-size: 14px; }
        th { color: #38bdf8; }
        select, input { width: 100%; padding: 8px; margin-top: 5px; margin-bottom: 15px; background: #0f172a; border: 1px solid #475569; color: white; border-radius: 5px; box-sizing: border-box; }
    </style>
</head>
<body>
    <div class="container">
        <h2>Rahul API Admin Panel</h2>
        <form action="/admin/create" method="POST">
            <label>Select Tier:</label>
            <select name="tier">
                <option value="free">Free (10 Requests Limit)</option>
                <option value="paid">Paid (Unlimited)</option>
            </select>
            <button type="button" class="btn" onclick="generateKey()">Generate Random Key</button>
            <input type="text" id="generated_key" name="key" placeholder="Click above to generate key..." required style="margin-top:10px;">
            <button type="submit" class="btn" style="background: #16a34a;">Save Key to Database</button>
        </form>

        <hr style="border-color: #334155; margin: 20px 0;">

        <h3>Active API Keys</h3>
        <table>
            <tr>
                <th>API Key</th>
                <th>Tier</th>
                <th>Requests Left</th>
                <th>Action</th>
            </tr>
            {% for key, data in keys.items() %}
            <tr>
                <td><b>{{ key }}</b></td>
                <td>{{ data.tier.upper() }}</td>
                <td>{{ data.requests_left }}</td>
                <td>
                    <form action="/admin/revoke" method="POST" style="margin:0;">
                        <input type="hidden" name="key" value="{{ key }}">
                        <button type="submit" class="btn btn-danger">Revoke</button>
                    </form>
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>

    <script>
        function generateKey() {
            // Random number 10 to 999
            const randNum = Math.floor(Math.random() * 990) + 10;
            const key = "rahul" + randNum;
            document.getElementById('generated_key').value = key;
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return jsonify({
        "message": "Welcome to Number Info API",
        "usage": "/api/YOUR_API_KEY/info?number=PHONE_NUMBER",
        "developer": "@Mr_Rahul_Dev"
    })

# Admin Panel Route
@app.route('/adminrahulop')
def admin_panel():
    return render_template_string(ADMIN_HTML, keys=API_KEYS_DB)

# Admin Key Creation Route
@app.route('/admin/create', methods=['POST'])
def admin_create():
    key = request.form.get('key')
    tier = request.form.get('tier')
    if key:
        limit = 10 if tier == 'free' else 999999
        API_KEYS_DB[key] = {"tier": tier, "requests_left": limit}
    return redirect(url_for('admin_panel'))

# Admin Key Revoke Route
@app.route('/admin/revoke', methods=['POST'])
def admin_revoke():
    key = request.form.get('key')
    if key in API_KEYS_DB:
        del API_KEYS_DB[key]
    return redirect(url_for('admin_panel'))

# Main Lookup API Endpoint
@app.route('/api/<key>/info', methods=['GET'])
def number_info(key):
    phone_number = request.args.get('number')
    
    if not key or key not in API_KEYS_DB:
        return jsonify({
            "status": False,
            "error": "Invalid or Missing API Key! Buy key from @Mr_Rahul_Dev"
        }), 403
    
    user_data = API_KEYS_DB[key]
    
    if user_data["tier"] == "free":
        if user_data["requests_left"] <= 0:
            return jsonify({
                "status": False,
                "error": "Free limit exhausted! Buy unlimited key from @Mr_Rahul_Dev"
            }), 429
        user_data["requests_left"] -= 1

    if not phone_number:
        return jsonify({"error": "Please provide ?number= parameter"}), 400

    if not phone_number.isdigit() and not (phone_number.startswith('+') and phone_number[1:].isdigit()):
        return jsonify({"error": "Invalid phone number format"}), 400

    try:
        url = "https://calltracer.in"
        headers = {
            "Host": "calltracer.in",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        payload = {
            "country": "IN",
            "q": phone_number
        }

        response = requests.post(url, headers=headers, data=payload, timeout=10)

        if response.status_code != 200:
            return jsonify({"error": f"Failed to fetch data. HTTP {response.status_code}"}), 500

        soup = BeautifulSoup(response.text, 'html.parser')

        def get_value(label):
            cell = soup.find(string=lambda t: t and label in t)
            if cell:
                td = cell.find_parent("tr")
                if td and td.find_all("td"):
                    tds = td.find_all("td")
                    if len(tds) > 1:
                        return tds[1].get_text(strip=True)
            return "N/A"

        scraped_data = {
            "Number": phone_number,
            "Complaints": get_value("Complaints"),
            "Owner Name": get_value("Owner Name"),
            "SIM Card": get_value("SIM card"),
            "Mobile State": get_value("Mobile State"),
            "IMEI Number": get_value("IMEI number"),
            "MAC Address": get_value("MAC address"),
            "Connection": get_value("Connection"),
            "IP Address": get_value("IP address"),
            "Owner Address": get_value("Owner Address"),
            "Hometown": get_value("Hometown"),
            "Reference City": get_value("Refrence City"),
            "Owner Personality": get_value("Owner Personality"),
            "Language": get_value("Language"),
            "Mobile Locations": get_value("Mobile Locations"),
            "Country": get_value("Country"),
            "Tracking History": get_value("Tracking History"),
            "Tracker ID": get_value("Tracker Id"),
            "Tower Locations": get_value("Tower Locations"),
        }

        if all(v == "N/A" for v in scraped_data.values()):
            data_content = {"message": "No data found for this number."}
        else:
            data_content = scraped_data

        response_payload = {
            "status": true,
            "query_number": phone_number,
            "data": data_content,
            "developer_info": {
                "developer": "@Mr_Rahul_Dev",
                "channel": "@Rahuls_Portal",
                "buy_api_from": "@Mr_Rahul_Dev"
            }
        }

        return jsonify(response_payload)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
