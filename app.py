"""
Flask routes
"""
from flask import Flask

app = Flask(__name__)


@app.route('/')
def live_test_scores_home():
    """Index route on app load."""
    return 'Hello world'


@app.route('/students')
def get_students():
    """Lists all users that have received at least one test score."""
    pass


@app.route('/students/<id>')
def get_student_id():
    """
    Lists the test results for the specified student, and provides the student's average score across all exams.
    """
    pass


@app.route('/exams')
def get_exams():
    """Lists all the exams that have been recorded."""
    pass


@app.route('/exams/<id>')
def get_exam_id():
    """Lists all the results for the specified exam, and provides the average score across all students."""
    pass
