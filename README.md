# Live Test Scores API

A Python Flask app that consumes events from a service `https://live-test-scores.herokuapp.com/scores` that uses a
[Server-Sent Events](https://html.spec.whatwg.org/multipage/server-sent-events.html#server-sent-events) protocol, 
processes them, and provides a simple REST API that exposes the processed results.

The JSON payload for one of these events looks like this:
```
event: score
data: {"exam": 3, "studentId": "foo", score: .991}
```

### App components

1. <b>Redis:</b> Serves as the broker for Celery to process the events and also as the in-memory database.
Database 0 is used for the broker connection, database 1 is used for storing students data, and database 1 is used for storing the exams data.
2. <b>Celery:</b> Continuously process the events asynchronously in the background as they come in from the SSE server endpoint.

## Endpoints

- `GET /students` -- Lists all users that have received at least one test score
- `GET /students/{id}` -- Lists the test results for the specified student, and provides the student's average score across all exams
- `GET /exams` -- Lists all the exams that have been recorded
- `GET /exams/{number}` -- Lists all the results for the specified exam, and provides the average score across all students

## How to run

1. Clone this repo and navigate to that directory

#### Docker

Using port 5001 for docker to view the application. The docker compose takes care of setting up celery and redis as well to start running the entire environment.

1. Install and setup [docker](https://docs.docker.com/get-docker/)
2. In the CLI, run `docker compose up --build`
3. Go to a browser: `http://127.0.0.1:5001/` to view the application

#### Native env

Using port 8000 if just running flask app without docker:

(You can also spin up a python environment: [pyenv](https://github.com/pyenv/pyenv)) before proceeding:

1. In the CLI: `pip install -r requirements.txt`
2. And then run `flask run --host 0.0.0.0 --port 8000`
3. In a separate CLI window, make sure the redis server is running: `redis-server`
4. In a separate CLI window, start the celery worker: `celery -A app.celery worker --loglevel=info`
5. Go to a browser: `http://127.0.0.1:8000/` to view the application

## Running tests

1. In the CLI, run `pip install -r requirements.txt` to install pytest
2. Then run `pytest`
