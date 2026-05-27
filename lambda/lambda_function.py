import json
import boto3
import sys
import os
from decimal import Decimal
from datetime import datetime, timezone

sys.path.insert(0, '/var/task')

dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
table = dynamodb.Table('ECUFaultHistory')

def convert_floats(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, dict):
        return {k: convert_floats(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_floats(i) for i in obj]
    return obj

def handler(event, context):
    print(f"Received event: {json.dumps(event)}")
    
    try:
        # ── Step 1: Import AI classifier
        from ai_classifier import classify_fault
        
        # ── Step 2: Get AI diagnosis
        print(f"Calling AI classifier for fault: {event.get('dtc_code')}")
        ai_diagnosis = classify_fault(event)
        print(f"AI diagnosis received: {ai_diagnosis.get('safety_risk')} risk")
        
        # ── Step 3: Build complete record
        record = {
            'fault_id':     event.get('fault_id', 'UNKNOWN'),
            'timestamp':    event.get('timestamp', datetime.now(timezone.utc).isoformat()),
            'vehicle_id':   event.get('vehicle_id', 'UNKNOWN'),
            'dtc_code':     event.get('dtc_code', 'UNKNOWN'),
            'description':  event.get('description', 'UNKNOWN'),
            'severity':     event.get('severity', 'UNKNOWN'),
            'sensor_data':  convert_floats(event.get('sensor_data', {})),
            'processed_at': datetime.now(timezone.utc).isoformat(),
            'ai_diagnosis': convert_floats(ai_diagnosis)
        }
        
        # ── Step 4: Store in DynamoDB
        table.put_item(Item=record)
        
        print(f"Stored: {record['fault_id']} — {record['dtc_code']} — Risk: {ai_diagnosis.get('safety_risk')}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Fault stored with AI diagnosis',
                'fault_id': record['fault_id'],
                'dtc_code': record['dtc_code'],
                'safety_risk': ai_diagnosis.get('safety_risk'),
                'mode': ai_diagnosis.get('mode')
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise e