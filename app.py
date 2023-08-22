"""
Flask routes for live test score retrieval
"""
import json
import sseclient
from flask import Flask, Response, jsonify
from db import RedisDB

app = Flask(__name__)
app.students_db = RedisDB(db=1)  # database for students
app.exams_db = RedisDB(db=2)  # database for exams


SCORES_SERVER_URL = "http://live-test-scores.herokuapp.com/scores"


def connect_to_server():
    client = sseclient.SSEClient(SCORES_SERVER_URL)

    for event in client:
        if event.event == 'score':
            row = json.loads(event.data)
            app.students_db.save_event(row.get('studentId'), row.get('exam'), row.get('score'))
            app.exams_db.save_event(row.get('exam'), row.get('studentId'), row.get('score'))
            yield f"data: {row}\n\n"


@app.route('/', methods=['GET'])
def live_test_scores_home():
    """Index route on app load."""
    return Response(connect_to_server(), content_type='text/event-stream')


@app.route('/students', methods=['GET'])
def get_students():
    """Lists all users that have received at least one test score."""
    students = app.students_db.get_keys()
    students = [s.decode() for s in students]
    return jsonify(students)


@app.route('/students/<student_id>', methods=['GET'])
def get_student_test_results(student_id):
    """
    Lists the test results for the specified student, and provides the student's average score across all exams.
    """
    test_results = app.students_db.get_event(student_id)
    avg_score = average_score(test_results)

    test_results = [e.decode() for e in test_results]
    return jsonify({'entries': test_results, 'avg_score': avg_score})


@app.route('/exams', methods=['GET'])
def get_exams():
    """Lists all the exams that have been recorded."""
    exams = app.exams_db.get_keys()
    exams = [e.decode() for e in exams]
    return jsonify(exams)


@app.route('/exams/<exam_id>', methods=['GET'])
def get_exam_results(exam_id):
    """Lists all the results for the specified exam, and provides the average score across all students."""
    test_results = app.exams_db.get_event(exam_id)
    avg_score = average_score(test_results)

    test_results = [e.decode() for e in test_results]
    return jsonify({'entries': test_results, 'avg_score': avg_score})


def average_score(results):
    avg_score = 0
    if len(results) > 0:
        total = sum(float(score) for _, score in results.items())
        avg_score = total / len(results)

    return avg_score
