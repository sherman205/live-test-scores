"""
Flask routes for live test score retrieval
"""
import json
import sseclient
from flask import Flask, Response, jsonify
from db import RedisDB

app = Flask(__name__)
app.scores_db = RedisDB(db=1)
app.exams_db = RedisDB(db=2)


SCORES_SERVER_URL = "http://live-test-scores.herokuapp.com/scores"


def connect_to_server():
    client = sseclient.SSEClient(SCORES_SERVER_URL)

    for event in client:
        if event.event == 'score':
            row = json.loads(event.data)
            app.scores_db.save_event(row.get('studentId'), row.get('exam'), row.get('score'))
            app.exams_db.save_event(row.get('exam'), row.get('studentId'), row.get('score'))
            yield f"data: {row}\n\n"


@app.route('/', methods=['GET'])
def live_test_scores_home():
    """Index route on app load."""
    return Response(connect_to_server(), content_type='text/event-stream')


@app.route('/students', methods=['GET'])
def get_students():
    """Lists all users that have received at least one test score."""
    students = app.scores_db.get_keys()
    students = [s.decode() for s in students]
    return jsonify(students)


@app.route('/students/<id>', methods=['GET'])
def get_student_id():
    """
    Lists the test results for the specified student, and provides the student's average score across all exams.
    """
    pass


@app.route('/exams', methods=['GET'])
def get_exams():
    """Lists all the exams that have been recorded."""
    pass


@app.route('/exams/<id>', methods=['GET'])
def get_exam_id():
    """Lists all the results for the specified exam, and provides the average score across all students."""
    pass
