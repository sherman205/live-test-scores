"""
Tests for app.py
"""
from app import app, average_score, celery, process_test_scores_data
from unittest import TestCase
from db import RedisDB

import json
import unittest
from unittest.mock import patch, call, Mock


@patch('app.sseclient.SSEClient')
@patch('app.app.students_db.save_event')
@patch('app.app.exams_db.save_event')
class TestProcessTestScoresData(unittest.TestCase):

	def test_process_test_scores_data(self, mock_save_exam, mock_save_student, mock_sseclient):
		"""
		Tests simulating processing data from an SSE server and adding the correct
		events to each mock database.
		"""
		# Mock SSE event data
		event_data = [
			Mock(event='score', data=json.dumps({
				'studentId': 'studentId12345',
				'exam': '150',
				'score': '0.90'
			})),
			Mock(event='score', data=json.dumps({
				'studentId': 'studentId56789',
				'exam': '180',
				'score': '0.70'
			}))
		]

		# Configure mock SSEClient behavior
		mock_sseclient.return_value.__iter__.return_value = iter(event_data)

		process_test_scores_data()

		self.assertEqual(mock_save_student.call_count, 2)
		self.assertEqual(mock_save_exam.call_count, 2)

		mock_save_student.assert_has_calls(
			calls=[call('studentId12345', '150', '0.90'), call('studentId56789', '180', '0.70')]
		)
		mock_save_exam.assert_has_calls(
			calls=[call('150', 'studentId12345', '0.90'), call('180', 'studentId56789', '0.70')]
		)

	def test_process_test_scores_incorrect_event(self, mock_save_exam, mock_save_student, mock_sseclient):
		"""Tests that no action is taken if the event type is not "score"."""
		# Mock SSE event data
		event_data = [
			Mock(event='test', data=json.dumps({
				'studentId': 'studentId12345',
				'name': 'Jill'
			}))
		]

		# Configure mock SSEClient behavior
		mock_sseclient.return_value.__iter__.return_value = iter(event_data)

		process_test_scores_data()

		mock_save_exam.assert_not_called()
		mock_save_student.assert_not_called()


class TestLiveTestResults(TestCase):

	def setUp(self):
		app.testing = True
		self.students_db = RedisDB(db=1)
		self.exams_db = RedisDB(db=2)

		self.student1 = 'studentId12345'
		self.student2 = 'studentId56789'
		self.exam1 = 'exam500'
		self.exam2 = 'exam501'

		self.students_db.save_event(self.student1, self.exam1, '0.80')
		self.students_db.save_event(self.student1, self.exam2, '0.70')
		self.students_db.save_event(self.student2, self.exam2, '0.90')
		self.exams_db.save_event(self.exam1, self.student1, '0.80')
		self.exams_db.save_event(self.exam2, self.student1, '0.70')
		self.exams_db.save_event(self.exam2, self.student2, '0.90')

	def tearDown(self):
		self.students_db.delete(self.student1)
		self.students_db.delete(self.student2)
		self.exams_db.delete(self.exam1)
		self.exams_db.delete(self.exam2)

	def test_index_route(self):
		"""Test that index (/) endpoint returns 200 status and expected message."""
		response = app.test_client().get('/')
		self.assertEqual(response.status_code, 200)
		self.assertIn(b'Live Test Results', response.data)

	def test_get_students(self):
		"""Test that all expected students are in the response data."""
		response = app.test_client().get('/students')
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.student1.encode(), response.data)
		self.assertIn(self.student2.encode(), response.data)

	def test_get_student_test_results(self):
		"""Test that for the specified student, only that student's exams and test scores are available."""
		response = app.test_client().get(f'/students/{self.student1}')
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.student1.encode(), response.data)
		self.assertNotIn(self.student2.encode(), response.data)
		self.assertIn(self.exam1.encode(), response.data)
		self.assertIn(self.exam2.encode(), response.data)
		self.assertIn(b'0.70', response.data)
		self.assertIn(b'0.80', response.data)
		# assert avg score
		self.assertIn(b'0.75', response.data)

	def test_exams(self):
		"""Test that all expected exams are in the response data."""
		response = app.test_client().get('/exams')
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.exam1.encode(), response.data)
		self.assertIn(self.exam2.encode(), response.data)

	def test_get_exam_results(self):
		"""Test that for the specified exam, only results for that exam is available."""
		response = app.test_client().get(f'/exams/{self.exam2}')
		self.assertEqual(response.status_code, 200)
		self.assertIn(self.exam2.encode(), response.data)
		self.assertNotIn(self.exam1.encode(), response.data)
		self.assertIn(self.student1.encode(), response.data)
		self.assertIn(self.student2.encode(), response.data)
		self.assertIn(b'0.70', response.data)
		self.assertIn(b'0.90', response.data)
		# assert avg score
		self.assertIn(b'0.8', response.data)


class TestHelpers(TestCase):

	def test_average_score(self):
		"""
		Tests that given a dictionary where the value is a float,
		it returns the correct average of the float values.
		"""
		test_results = {'studentId12345': '0.90', 'studentId56789': '0.70'}
		avg_score = average_score(test_results)
		self.assertEqual(avg_score, 0.8)

	def test_average_score_empty_dict(self):
		"""Tests that when a dictionary is empty, average score returned is 0."""
		avg_score = average_score({})
		self.assertEqual(avg_score, 0)
