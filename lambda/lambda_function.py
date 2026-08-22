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

def process_fault(fault_data):
    from ai_classifier import classify_fault

    ai_diagnosis = classify_fault(fault_data)

    record = {
        'fault_id':     fault_data.get('fault_id', 'UNKNOWN'),
        'timestamp':    fault_data.get('timestamp',
                        datetime.now(timezone.utc).isoformat()),
        'vehicle_id':   fault_data.get('vehicle_id', 'UNKNOWN'),
        'dtc_code':     fault_data.get('dtc_code', 'UNKNOWN'),
        'description':  fault_data.get('description', 'UNKNOWN'),
        'severity':     fault_data.get('severity', 'UNKNOWN'),
        'sensor_data':  convert_floats(fault_data.get('sensor_data', {})),
        'processed_at': datetime.now(timezone.utc).isoformat(),
        'ai_diagnosis': convert_floats(ai_diagnosis)
    }

    table.put_item(Item=record)
    print(f"Stored: {record['fault_id']} — {record['dtc_code']}")

def handler(event, context):
    # SQS delivers messages in batches via Records array
    records = event.get('Records', [])
    print(f"Received {len(records)} record(s) from SQS")

    for record in records:
        try:
            # Unwrap SQS — body contains the original IoT fault message
            fault_data = json.loads(record['body'])
            print(f"Processing: {fault_data.get('dtc_code')} "
                  f"from {fault_data.get('vehicle_id')}")
            process_fault(fault_data)

        except Exception as e:
            print(f"Error processing record: {str(e)}")
            raise e  # re-raise so SQS knows to retry this message

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Processed {len(records)} fault(s)'
        })
    }