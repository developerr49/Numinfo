from flask import Flask, request, jsonify, render_template_string, redirect, url_for
import requests
from bs4 import BeautifulSoup
import os
import random
import sqlite3

app = Flask(__name__)

DB_FILE = "keys.db"

# Database Initialize Function
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS api_keys (
            key TEXT PRIMARY KEY,
            tier TEXT,
            requests_left INTEGER
        )
    ''')
    cursor.execute("INSERT OR IGNORE INTO api_keys (key, tier, requests_left) VALUES ('rahul748', 'free', 10)")
    cursor.execute("INSERT OR IGNORE INTO api_keys (key, tier, requests_left) VALUES ('rahul999', 'paid', 999999)")
    conn.commit()
    conn.close()

init_db()

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
            {% for key, tier, requests_left in keys %}
            <tr>
                <td><b>{{ key }}</b></td>
                <td>{{ tier.upper() }}</td>
                <td>{{ requests_left }}</td>
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

@app.route('/adminrahulop')
def admin_panel():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT key, tier, requests_left FROM api_keys")
    keys = cursor.fetchall()
    conn.close()
    return render_template_string(ADMIN_HTML, keys=keys)

@app.route('/admin/create', methods=['POST'])
def admin_create():
    key = request.form.get('key')
    tier = request.form.get('tier')
    if key:
        limit = 10 if tier == 'free' else 999999
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO api_keys (key, tier, requests_left) VALUES (?, ?, ?)", (key, tier, limit))
        conn.commit()
        conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/admin/revoke', methods=['POST'])
def admin_revoke():
    key = request.form.get('key')
    if key:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM api_keys WHERE key = ?", (key,))
        conn.commit()
        conn.close()
    return redirect(url_for('admin_panel'))

@app.route('/api/<key>/info', methods=['GET'])
def number_info(key):
    phone_number = request.args.get('number')
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT tier, requests_left FROM api_keys WHERE key = ?", (key,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return jsonify({
            "status": False,
            "error": "Invalid or Missing API Key! Buy key from @Mr_Rahul_Dev"
        }), 403
    
    tier, requests_left = row
    
    if tier == "free":
        if requests_left <= 0:
            conn.close()
            return jsonify({
                "status": False,
                "error": "Free limit exhausted! Buy unlimited key from @Mr_Rahul_Dev"
            }), 429
        requests_left -= 1
        cursor.execute("UPDATE api_keys SET requests_left = ? WHERE key = ?", (requests_left, key))
        conn.commit()
    
    conn.close()

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
            "Reference City": get_value("Reference City"),
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
            "status": True,
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
