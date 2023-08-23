"""
Tests for app.py
"""
from app import app
from unittest import TestCase
from db import RedisDB


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
