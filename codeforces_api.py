import os
import random
import requests

from bs4 import BeautifulSoup
from rq import Queue
from redis import Redis
from dotenv import load_dotenv
from datetime import timedelta
from utils import sign, unpack
from dotenv import load_dotenv
from rq import Queue

import logging, sys

load_dotenv()

BASE = "https://codeforces.com"
SUBMIT_URL = f"{BASE}/problemset/submit"
LOGIN_URL = f"{BASE}/enter"
SUBMISSION_URL = f"{BASE}/submissions"
MAX_ATTEMPTS = os.getenv('MAX_ATTEMPTS')
ACCELERATION = int(os.getenv('ACCELERATION'))
INTERVAL = int(os.getenv('INTERVAL'))
ONLINE_JUDGE = os.getenv('ONLINE_JUDGE')
JOB_TIMEOUT = int(os.getenv('JOB_TIMEOUT'))
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = int(os.getenv('REDIS_PORT'))


SUBMISSION_VERDICT = {
    'Time limit exceeded': 'TLE',
    'Runtime error': 'RTE',
    'Memory limit exceeded': 'MLE',
    'Wrong answer': 'WA',
    'Accepted': 'AC',
    'Compilation error': 'CE'
}

LANGUAGE_CODE = {
    'C': 43,
    'C11': 43,
    'PY3': 70,
    'CPP14': 50,
    'CPP17': 54,
    'CPP20': 73
}

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

def error(submission_id: str, err = 'ERR'):
    logging.error(f" Submission {submission_id}: {err}")

    data = {
        'submission_id': submission_id,
        'verdict': 'ERR'
    }
    data = sign(data)

    requests.post(ONLINE_JUDGE, json = data)

def login(username: str, password: str):
    session = requests.session()

    try:
        parser = BeautifulSoup(requests.get(LOGIN_URL).text, 'html.parser')
        csrf_token = parser.find_all("span", {"class": "csrf-token"})[0]["data-csrf"]
    except:
        return None

    headers = {
        'X-Csrf-Token': csrf_token
    }

    payload = {
        'csrf_token': csrf_token,
        'action': 'enter',
        'handleOrEmail': username,
        'password': password,
    }

    login_request = session.post(LOGIN_URL, data = payload, headers = headers)

    return session


def submit(source: str, problem_code: str, language: str, submission_id: str, username: str, password: str, queue_name: str):
    logging.info(f"Queue {queue_name}: Received submission {submission_id} for problem {problem_code}")
    
    try:
        redis_conn = Redis(host=REDIS_HOST, port=REDIS_PORT)
        queue = Queue(queue_name, connection = Redis())

        session = login(username, password)

        if not session:
            error(submission_id, 'Could not login!')
            return None

        parser = BeautifulSoup(requests.get(SUBMIT_URL).text, 'html.parser')

        csrf_token = parser.find_all("span", {"class": "csrf-token"})[0]["data-csrf"]
    except:
        error(submission_id, 'Could not load submit page.')
        return None

    payload = {
        'csrf_token': csrf_token,
        'action': 'submitSolutionFormSubmitted',
        'submittedProblemCode': problem_code,
        'programTypeId': LANGUAGE_CODE.get(language, 50),
        'tabSize': 4,
        'source': source,
        '_tta': 99 
    }

    try:
        submit_request = session.post(SUBMIT_URL, data = payload)
        parser = BeautifulSoup(submit_request.text, 'html.parser')
        submission = parser.find_all("tr", limit = 2)[1]['data-submission-id']
    except:
        error(submission_id, 'Could not submit! Possibly due to repeated code.')
        return None

    queue.enqueue_in(
        timedelta(seconds=INTERVAL),
        get_submission,
        submission,
        submission_id,
        problem_code,
        0,
        queue_name,
        job_timeout = JOB_TIMEOUT
    )

def get_verdict(verdict):
    for key, value in SUBMISSION_VERDICT.items():
        if key in verdict:
            return value

    return 'WA'

def get_submission(submission: str, submission_id: str, problem_code: str, attempt_count: int, queue_name: str):
    redis_conn = Redis(host=REDIS_HOST, port=REDIS_PORT)
    queue = Queue(queue_name, connection = redis_conn)

    session = requests.session()

    try:
        submission_url = f"{BASE}/contest/{problem_code[:-1]}/submission/{submission}"
        get_submission_request = session.get(submission_url)
        parser = BeautifulSoup(get_submission_request.text, 'html.parser')
        result = parser.find_all('tr', limit = 2)[1].find_all('td')

        verdict = result[4].text.strip()
        time = result[5].text.strip()
        memory = result[6].text.strip()
    except:
        queue.enqueue_in(
            timedelta(seconds = INTERVAL + attempt_count * ACCELERATION),
            get_submission,
            submission,
            submission_id,
            problem_code,
            attempt_count,
            queue_name,
            job_timeout = JOB_TIMEOUT
        )

    if (len(verdict) > 7 and verdict[:7] == "Running") or verdict == "In queue" or attempt_count == MAX_ATTEMPTS:
        attempt_count += 1
        queue.enqueue_in(
            timedelta(seconds = INTERVAL + attempt_count * ACCELERATION),
            get_submission,
            submission,
            submission_id,
            problem_code,
            attempt_count,
            queue_name,
            job_timeout = JOB_TIMEOUT
        )
    else:
        data = {
            'submission_id': submission_id,
            'verdict': get_verdict(verdict),
            'time': int(time.split()[0]),
            'memory': int(memory.split()[0])
        }

        data = sign(data)
        requests.post(ONLINE_JUDGE, json = data)

        logging.info(f"Queue {queue_name}: Submitted result {verdict}, time: {time}, memory: {memory} - submission {submission_id} for problem {problem_code}")