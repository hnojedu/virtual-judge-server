<h1 style="text-align:center">Suika Virtual Judge Server</h1>
<div style="width:100%" align="center">
<img src="https://i.imgur.com/U35v4WU.png" style="width:50%">
</div>

### Too Lazy for Codeforces Testcases?
Indirectly submit Codeforces problems using this tool! Look forward to added support for more online judges in the future.

## Installation

### Step 1: Clone the Repository

Begin by cloning the repository:
```
$ git clone https://github.com/hnojedu/virtual-judge-server.git
$ cd virtual-judge-server
```

### Step 2: Install Dependencies

Install the required dependencies using pip:
```
$ pip install -r requirements.txt
```

### Step 3: Start Redis Server

Initiate the Redis server:
```
$ sudo systemctl start redis-server
```
Ensure that the Redis server is operational by running:

```
$ redis-cli ping
```

You should receive a response of `PONG`.

### Step 4: Configuration

Create a copy of the example configuration file:
```
$ cp env.example .env
```

#### Configuration Settings

- `KEY`: A 64-character key, obtainable by running `$ python3 generate_key.py`. This should match `JUDGE_SERVER_KEY` in the online judge server.
- `USERNAME, PASSWORD`: Codeforces account credentials (separated by commas).
- `INTERVAL`: Time interval between requests in seconds. Be cautious not to set this too low, as it may result in Codeforces blocking your requests.
- `ACCELERATION`: The increment in the time interval after each request, specified in seconds.
- `MAX_ATTEMPTS`: The maximum number of attempts to retrieve submission results.
- `ONLINE_JUDGE`: URL of the online judge platform where the server will send results.
- `JOB_TIMEOUT`: Timeout duration for each request in seconds.
- `REDIS_HOST`: Redis server hostname.
- `REDIS_PORT`: Redis server port.

### Step 5: Run the Server

Initiate the server with the following command:

```
python3 judge.py
```

This will start the server using Flask's built-in server, running on the host defined by `APPLICATION_HOST` and port `APPLICATION_PORT` in configuration file. If necessary, you can use more advanced web servers like Gunicorn or uWSGI.