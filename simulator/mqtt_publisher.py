import paho.mqtt.client as mqtt
import ssl
import json
import time
import random
from datetime import datetime, timezone
from dotenv import load_dotenv
import os

load_dotenv()

# Load config
with open("simulator/iot_config.json") as f:
    config = json.load(f)

# Fault codes to simulate
FAULT_CODES = [
    {"code": "P0300", "description": "Random Cylinder Misfire", "severity": "High"},
    {"code": "P0115", "description": "Engine Coolant Temp Sensor Fault", "severity": "Medium"},
    {"code": "P0562", "description": "System Voltage Low", "severity": "High"},
    {"code": "U0100", "description": "Lost Communication With ECM", "severity": "Critical"},
    {"code": "P0171", "description": "System Too Lean Bank 1", "severity": "Medium"},
]

def generate_fault_message():
    fault = random.choice(FAULT_CODES)
    return {
        "fault_id": f"FAULT-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{random.randint(100,999)}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "vehicle_id": "VH-SIM-001",
        "dtc_code": fault["code"],
        "description": fault["description"],
        "severity": fault["severity"],
        "sensor_data": {
            "RPM": random.randint(800, 4000),
            "coolant_temp_c": round(random.uniform(70, 120), 1),
            "battery_voltage": round(random.uniform(11.0, 14.8), 2)
        }
    }

# MQTT callbacks
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ Connected to AWS IoT Core successfully")
    else:
        print(f"❌ Connection failed with code {rc}")

def on_publish(client, userdata, mid, rc=None, properties=None):
    print(f"📤 Message published successfully (mid: {mid})")

# Set up MQTT client
client = mqtt.Client(
    client_id=config["client_id"],
    protocol=mqtt.MQTTv5
)

client.on_connect = on_connect
client.on_publish = on_publish

# Configure TLS with certificates
client.tls_set(
    ca_certs=config["ca_path"],
    certfile=config["cert_path"],
    keyfile=config["key_path"],
    tls_version=ssl.PROTOCOL_TLS_CLIENT
)

# Connect
print(f"🔌 Connecting to {config['endpoint']}...")
client.connect(config["endpoint"], config["port"], keepalive=60)
client.loop_start()

# Wait for connection
time.sleep(2)

# Publish fault messages every 5 seconds
print(f"🚗 Starting ECU fault simulator — publishing to topic: {config['topic']}")
print("Press Ctrl+C to stop\n")

try:
    while True:
        message = generate_fault_message()
        payload = json.dumps(message, indent=2)
        client.publish(config["topic"], payload, qos=1)
        print(f"[{message['timestamp']}] Fault: {message['dtc_code']} — {message['description']} ({message['severity']})")
        time.sleep(5)

except KeyboardInterrupt:
    print("\n🛑 Simulator stopped")
    client.loop_stop()
    client.disconnect()