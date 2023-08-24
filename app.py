"""
Flask routes for live test score retrieval
"""
import os
import json
import sseclient
import markdown
from flask import Flask, render_template
from celery import Celery
from db import RedisDB


app = Flask(__name__)

# Configure Celery
host_name = os.environ.get("REDIS_HOST", "localhost")
app.config['CELERY_BROKER_URL'] = f'redis://{host_name}:6379/0'
app.config['result_backend'] = f'redis://{host_name}:6379/0'
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

app.students_db = RedisDB(host=host_name, db=1)  # database for students
app.exams_db = RedisDB(host=host_name, db=2)  # database for exams

SCORES_SERVER_URL = "http://live-test-scores.herokuapp.com/scores"


@celery.task
def process_test_scores_data():
    """Connects to SSE server to process test results and save to Redis db in memory."""
    client = sseclient.SSEClient(SCORES_SERVER_URL)

    for event in client:
        if event.event == 'score':
            row = json.loads(event.data)
            app.students_db.save_event(row.get('studentId'), row.get('exam'), row.get('score'))
            app.exams_db.save_event(row.get('exam'), row.get('studentId'), row.get('score'))

            # Output for celery queue
            print(f"data: {row}\n\n")


# Start processing data from SSE server on app start up
with app.app_context():
    process_test_scores_data.apply_async()


# =========== Routes ==============#

@app.route('/', methods=['GET'])
def live_test_scores_home():
    """Index route on app load, displays the README."""
    with open('README.md', 'r') as readme_file:
        readme_content = readme_file.read()
        html_content = markdown.markdown(readme_content)

    return render_template('welcome.html', content=html_content)


@app.route('/students', methods=['GET'])
def get_students():
    """Lists all students that have received at least one test score."""
    students = app.students_db.get_keys()
    students = [s.decode() for s in students]
    return render_template('students.html', students=students)


@app.route('/students/<student_id>', methods=['GET'])
def get_student_test_results(student_id):
    """
    Lists the test results for the specified student, and provides the student's average score across all exams.
    """
    test_results = app.students_db.get_event(student_id)
    avg_score = average_score(test_results)
    return render_template('student_scores.html', student_id=student_id,
                           test_results=test_results, avg_score=avg_score)


@app.route('/exams', methods=['GET'])
def get_exams():
    """Lists all the exams that have been recorded."""
    exams = app.exams_db.get_keys()
    exams = [e.decode() for e in exams]
    return render_template('exams.html', exams=exams)


@app.route('/exams/<exam_id>', methods=['GET'])
def get_exam_results(exam_id):
    """Lists all the results for the specified exam, and provides the average score across all students."""
    test_results = app.exams_db.get_event(exam_id)
    avg_score = average_score(test_results)
    return render_template('exam_scores.html', exam_id=exam_id,
                           test_results=test_results, avg_score=avg_score)

# ============= Helpers =============== #


def average_score(results: dict) -> float:
    """Calculate average score given a dictionary of test results."""
    avg_score = 0
    if len(results) > 0:
        total = sum(float(score) for _, score in results.items())
        avg_score = total / len(results)

    return avg_score
