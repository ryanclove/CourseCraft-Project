import pytest
import sqlalchemy
import pandas as pd
from web.data.dbconnector import DBConnector

db = DBConnector()


# gets id of test studen
@pytest.fixture
def user_id():
    query = f"SELECT id FROM users WHERE email='test_student@rutgers.edu'"
    id = db._execute_select(query).iloc[0][0]
    return id


# gets assignment id for test assignment
@pytest.fixture
def assignment_id():
    query = f"SELECT assignment_id FROM assignments WHERE assignment_name='test_assignment' "
    result = db._execute_select(query).iloc[0][0]
    return result


# sets up the default student, class, and assignment
def test_setup_defaults():
    db.create_user('test_student@rutgers.edu', 'test', 'Student', 'test_student', 'CS')
    db.create_class('test_class', 'CS', 'Monday', '2020-05-05', '2020-01-01', '12:00:00', '13:20:00')
    db.create_assignments('test_assignment', 'test_file', 'test_class', '2050-01-01 00:00:00')


# test student registering for a class
def test_register(user_id):
    courses = ['test_class']
    result = db.course_registration(courses, user_id)


# test a student getting an assignment
def test_get_assignments():
    df = db.get_assignments('test_class')
    found = [df.eq('test_assignment').any(1)]
    if found:
        found = True
    else:
        found = False
    assert found == True


# tests a student submitting an assignment
def test_submit_assignment(assignment_id, user_id):
    result = db.submit_assignments(assignment_id, user_id, "test_submission")


# clears the default student, class, and assignment from the database
def test_remove_defaults():
    query = f"DELETE FROM users WHERE email='test_student@rutgers.edu'"
    db._execute_insert(query)
    query = f"DELETE FROM classes WHERE class_name='test_class'"
    db._execute_insert(query)
    query = f"DELETE FROM assignments WHERE assignment_name='test_assignment'"
    db._execute_insert(query)
