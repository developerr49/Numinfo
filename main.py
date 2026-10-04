from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

# API Keys Database (Free aur Paid keys ke liye limits)
API_KEYS_DB = {
    "rahul_748_free": {"tier": "free", "requests_left": 5},
    "rahul_vip_9999": {"tier": "paid", "requests_left": 999999}
}

@app.route('/')
def home():
    return jsonify({
        "message": "Welcome to Number Info API",
        "usage": "/info?number=PHONE_NUMBER&key=YOUR_API_KEY",
        "channel": "@Rahuls_Portal"
    })


@app.route('/info', methods=['GET'])
def number_info():
    phone_number = request.args.get('number')
    api_key = request.args.get('key')
    
    # 1. API Key Check karein
    if not api_key or api_key not in API_KEYS_DB:
        return jsonify({
            "status": False,
            "error": "Invalid or Missing API Key! Buy key from @Mr_Rahul_Dev"
        }), 403
    
    user_data = API_KEYS_DB[api_key]
    
    # 2. Free Users ke liye Daily/Request Limit Check karein
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

        # Send POST request to source
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

        # 3. Custom Response with Developer Credits at the bottom
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
