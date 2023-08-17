from flask import Flask, request, jsonify
from redis import Redis
from rq import Queue
from dotenv import load_dotenv
from random import randrange
from utils import unpack
from flask import Response


import codeforces_api
import hashlib
import hmac
import os

load_dotenv()
SHARED_KEY = os.getenv('KEY')
USERNAME = os.getenv('USERNAME').split(',')
PASSWORD = os.getenv('PASSWORD').split(',')
JOB_TIMEOUT = int(os.getenv('JOB_TIMEOUT'))
NUM_QUEUES = int(os.getenv('NUM_QUEUES'))
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = int(os.getenv('REDIS_PORT'))
APPLICATION_PORT = int(os.getenv('APPLICATION_PORT'))

redis_conn = Redis(host=REDIS_HOST, port=REDIS_PORT)
queues = [Queue( str(_),connection=redis_conn) for _ in range(NUM_QUEUES)]
app = Flask(__name__)

@app.route("/judge", methods=['POST']) 
def judge():
    submission = unpack(request.get_json())

    if not submission:
        return Response(status = 403)

    queue_id = randrange(0, NUM_QUEUES)
    queue = queues[queue_id]

    result = queue.enqueue(
        codeforces_api.submit,
        submission['source'],
        submission['problem_code'],
        submission['language'],
        submission['submission'],
        USERNAME[queue_id],
        PASSWORD[queue_id],
        queue.name,
        job_timeout = 15
    )

    if result:
        return Response(status = 200)

    return Response(status = 500)

if __name__ == "__main__":
    app.run(host = "localhost", port = 6969, debug=True)