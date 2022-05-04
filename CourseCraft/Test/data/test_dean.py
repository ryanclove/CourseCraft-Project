import pytest
from web.data.dbconnector import DBConnector

db = DBConnector()


# Test the create user function for the dean role
def test_create_defaults():
    # Creates a test Dean user
    db.create_user("test@dean.com", "password", "dean", "test dean")


# Tests the deans create class function
def test_create_class():
    # Dean creates a test class
    db.create_class('Test Dean Class', 'Math', 'Monday', '2020-05-05', '2020-01-01', '12:00:00', '13:20:00')


# Clean up default test data
def test_cleanup_defaults():
    query = f"Delete FROM users WHERE email='test@dean.com'"
    db._execute_insert(query)

    query = f"Delete FROM classes WHERE class_name='Test Dean Class'"
    db._execute_insert(query)
