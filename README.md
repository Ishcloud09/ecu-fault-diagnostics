# ECU Fault Diagnostics — AI-Assisted Pipeline

A system that simulates CAN bus vehicle fault data, streams it to 
AWS IoT Core in real time, and uses AI to automatically classify 
and explain ECU fault codes — mimicking the diagnostic automation 
used by automotive OEMs for connected vehicle fleets.

## Problem It Solves
Modern connected vehicle fleets generate millions of fault events 
daily. Manual diagnosis by technicians cannot scale — a single 
fault takes 15–45 minutes to diagnose manually. This pipeline 
automates fault classification and root cause analysis using AI, 
reducing diagnostic time to under 3 seconds per fault.

## Architecture
Python CAN Simulator
↓  MQTT over TLS (port 8883)
AWS IoT Core (simulated-ecu-01)
↓  IoT Rule: SELECT * FROM 'ecu/faults'
AWS Lambda (ecu-fault-processor)
↓  Float conversion + record building
Claude/OpenAI API  ←→  AI fault classification
↓  Structured diagnosis returned
AWS DynamoDB (ECUFaultHistory)
↓  Fault history + AI diagnosis stored
AWS CloudWatch + SNS  →  Pipeline monitoring + email alerts

**Data flow:**
1. Python simulator generates realistic CAN bus fault codes and sensor data
2. Messages published to AWS IoT Core via MQTT over mutual TLS authentication
3. IoT Rule routes every message to Lambda using SQL: `SELECT * FROM 'ecu/faults'`
4. Lambda processes the fault, calls AI API for diagnosis, stores complete record in DynamoDB
5. CloudWatch monitors Lambda errors and alerts via email if pipeline breaks

## Tech Stack
| Component | Technology |
|---|---|
| CAN Simulator | Python + cantools + paho-mqtt |
| Cloud Messaging | AWS IoT Core + MQTT (port 8883) |
| Serverless Processing | AWS Lambda (Python 3.11) |
| AI Fault Classification | Claude API / OpenAI GPT-4 |
| Fault History Storage | AWS DynamoDB |
| Infrastructure as Code | Terraform |
| CI/CD Pipeline | GitHub Actions |
| Monitoring | AWS CloudWatch + SNS Alerts |

## Pipeline Status
✅ Phase 1 — CAN simulator generating realistic fault data  
✅ Phase 2 — AWS IoT Core receiving messages via MQTT/TLS  
✅ Phase 3 — Lambda processing and storing fault records  
✅ Phase 4 — DynamoDB storing 195+ fault records  
✅ Phase 5 — CloudWatch monitoring with email alerts  
🔧 Phase 6 — AI classification layer (in progress)  
⏳ Phase 7 — Terraform IaC + GitHub Actions CI/CD  

## Sample Fault Record
```json
{
  "fault_id": "FAULT-20260518172326-206",
  "timestamp": "2026-05-18T17:23:26+00:00",
  "vehicle_id": "VH-SIM-001",
  "dtc_code": "P0300",
  "description": "Random Cylinder Misfire",
  "severity": "High",
  "sensor_data": {
    "RPM": 1574,
    "coolant_temp_c": 116.4,
    "battery_voltage": 12.55
  },
  "processed_at": "2026-05-18T17:23:26.891+00:00",
  "ai_diagnosis": "PENDING"
}
```
## Prerequisites
- Python 3.10+
- AWS account (free tier sufficient)
- AWS CLI configured (`aws configure`)
- AWS IoT Core device certificate and keys

## How to Run
```bash
# Clone the repo
git clone git clone https://github.com/Ishcloud09/ecu-fault-diagnostics.git
cd ecu-fault-diagnostics

# Install dependencies
pip install -r requirements.txt

# Configure AWS credentials
aws configure

# Run the simulator
python simulator/mqtt_publisher.py
```

## Portfolio Context
Built to demonstrate the embedded + cloud + AI intersection 
relevant to connected vehicle roles at JLR, Caterpillar, Bosch, 
and automotive Tier 1 suppliers. All infrastructure simulated 
in Python — no physical hardware required.

## Author
Iswarya Thiagarajan  
linkedin.com/in/iswaryathiagarajan091096