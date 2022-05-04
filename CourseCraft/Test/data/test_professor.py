import pytest
import pandas as pd

from web.data.dbconnector import DBConnector

db = DBConnector()


# Fixture to represent a user id
@pytest.fixture
def user_id():
    query = f"SELECT id FROM users WHERE email='test@professor.com'"
    id = db._execute_select(query).iloc[0][0]
    return id


# Create default test data
def test_setup_defaults():
    # Creates a test Professor user for course registration
    db.create_user("test@professor.com", "password", "professor", "test professor")
    # Creates a test class for assignment creation
    db.create_class('Test Professor Class', 'CS', 'Monday', '2020-05-05', '2020-01-01', '12:00:00', '13:20:00')


# Test Professor create assignment function
# Called in prof_lecture.py
def test_create_assignment():
    db.create_assignments("Test Professor Assignment", "test_prof_file", "Test Professor Class", "2022-04-24 00:12:00")


# Test professor teach class function
def test_teach_class(user_id):
    db.teach_class(user_id, "Test Professor Class")


# Test find empty classes function
def test_find_empty_classes():
    result = db.find_empty_classes()
    assert not result.empty


# Test Professor get assignments
def test_get_assignments():
    result = db.get_assignments("Test Professor Class")
    assert not result.empty


# Remove test data from db
def test_cleanuo_defaults():
    query = f"Delete FROM users WHERE email='test@professor.com'"
    db._execute_insert(query)

    query = f"Delete FROM classes WHERE class_name='Test Professor Class'"
    db._execute_insert(query)

    query = f"Delete FROM teaches WHERE teaches_class_name='Test Professor Class'"
    db._execute_insert(query)

    query = f"Delete FROM assignments WHERE assignment_name='Test Professor Assignment'"
    db._execute_insert(query)
