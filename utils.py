import hashlib
import json
import hmac
import os
from dotenv import load_dotenv


load_dotenv()
SHARED_KEY = os.getenv('KEY')

def sign(data):
    data_str = json.dumps(data)
    data_bytes = data_str.encode('utf-8')
    

    signature = hmac.new(bytes(SHARED_KEY, encoding = 'utf-8'), data_bytes, hashlib.sha256).hexdigest()

    data = {
        'data': data_str,
        'signature': signature
    }

    return data

def unpack(received_data):
    data = received_data['data']
    received_signature = received_data['signature']

    submission_bytes = data.encode('utf-8')

    calculated_signature = hmac.new(bytes(SHARED_KEY, encoding = 'utf-8'), submission_bytes, hashlib.sha256).hexdigest()

    if received_signature != calculated_signature:
        return None

    return json.loads(data)