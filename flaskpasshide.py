import os
from flask import Flask, request, jsonify, render_template
from twilio.rest import Client
from flask_cors import CORS
import uuid
from datetime import datetime
import logging

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins for development

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# In-memory storage for SOS requests
sos_requests = {}

# Twilio Credentials (Replace with actual credentials)
TWILIO_ACCOUNT_SID =  "Axxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_AUTH_TOKEN = "axxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
TWILIO_PHONE_NUMBER = "+12xxxxxxxxxxx"
EMERGENCY_CONTACT_NUMBER = "+91xxxxxxxxxx"  # Replace with actual emergency contact number

# Initialize Twilio Client
twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    try:
        twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        logger.info("Twilio client initialized successfully")
    except Exception as e:
        logger.error(f"Twilio initialization failed: {e}")

@app.route('/')
def sender():
    return render_template('sender.html')

@app.route('/receiver')
def receiver():
    return render_template('receiver.html')

@app.route('/send_sos', methods=['POST'])
def send_sos():
    try:
        data = request.get_json()
        logger.debug(f"Received SOS data: {data}")

        if not data:
            return jsonify({'status': 'error', 'message': 'No data received'}), 400

        sos_id = str(uuid.uuid4())

        # Create SOS request
        sos_request = {
            'id': sos_id,
            'name': data.get('name', 'Anonymous'),
            'type': data.get('type', 'Help'),
            'latitude': data.get('latitude', 'N/A'),
            'longitude': data.get('longitude', 'N/A'),
            'address': data.get('address', 'Unknown'),
            'timestamp': datetime.now().isoformat(),
            'status': 'active'
        }

        # Store SOS request
        sos_requests[sos_id] = sos_request

        # Send SMS via Twilio
        if twilio_client:
            map_link = f"https://maps.google.com?q={sos_request['latitude']},{sos_request['longitude']}"
            sms_body = f"""🚨 Emergency Alert 🚨
Name: {sos_request['name']}
Type: {sos_request['type']} Emergency
Location: {map_link}"""

            try:
                message = twilio_client.messages.create(
                    body=sms_body,
                    from_=TWILIO_PHONE_NUMBER,
                    to=EMERGENCY_CONTACT_NUMBER
                )
                logger.info(f"SMS sent successfully! SID: {message.sid}, Status: {message.status}")
            except Exception as e:
                logger.error(f"SMS sending failed: {e}")

        return jsonify({'status': 'success', 'sos_id': sos_id}), 200

    except Exception as e:
        logger.error(f"Error in send_sos: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/get_sos', methods=['GET'])
def get_sos():
    try:
        active_requests = [request for request in sos_requests.values() if request['status'] == 'active']
        logger.debug(f"Returning {len(active_requests)} active SOS requests")
        return jsonify(active_requests), 200
    except Exception as e:
        logger.error(f"Error in get_sos: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/resolve_sos', methods=['POST'])
def resolve_sos():
    try:
        data = request.get_json()
        sos_id = data.get('sos_id')

        if not sos_id:
            return jsonify({'status': 'error', 'message': 'No SOS ID provided'}), 400

        if sos_id in sos_requests:
            sos_request = sos_requests[sos_id]
            sos_request['status'] = 'resolved'

            # Send resolution SMS
            if twilio_client:
                try:
                    message = twilio_client.messages.create(
                        body=f"🟢 SOS Resolved: {sos_request['name']}'s {sos_request['type']} Emergency",
                        from_=TWILIO_PHONE_NUMBER,
                        to=EMERGENCY_CONTACT_NUMBER
                    )
                    logger.info(f"Resolution SMS sent! SID: {message.sid}, Status: {message.status}")
                except Exception as e:
                    logger.error(f"Resolution SMS sending failed: {e}")

            return jsonify({'status': 'success'}), 200

        return jsonify({'status': 'error', 'message': 'SOS not found'}), 404

    except Exception as e:
        logger.error(f"Error in resolve_sos: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
