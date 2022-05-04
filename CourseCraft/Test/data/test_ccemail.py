from email.headerregistry import Address
from email.message import EmailMessage
from typing import List

import pandas as pd
import pytest

from web.data import ccemail


# Convert a list of messages to a list of message strings to allow for direct comparison
def _serialize_messages(msg_queue: List[EmailMessage]):
    return list(map(lambda x: x.as_string(), msg_queue))


# Fixture for mock student emails "student1@domain", "student2@domain", ...
@pytest.fixture
def student_emails():
    return [f"student{x}@domain" for x in range(1, 4)]


# Fixture for mock student names "Student 1", "Student 2", ...
@pytest.fixture
def student_names():
    return [f"Student {x}" for x in range(1, 4)]


# Mock ccemail._get_class_emails to create a set of test student data
@pytest.fixture
def mock_get_class_emails(monkeypatch, student_emails, student_names):
    def mock(*args, **kwargs):
        return pd.DataFrame(
            {
                "id": [1, 2, 3],
                "email": student_emails,
                "full_name": student_names,
            }
        )

    monkeypatch.setattr(ccemail, "_get_class_emails", mock)


# Mock ccemail._get_assignment_data to create a test assignment
@pytest.fixture
def mock_get_assignment_data(monkeypatch):
    def mock(*args, **kwargs):
        return pd.DataFrame(
            {
                "assignment_id": [1],
                "assignment_name": ["Test Assignment"],
                "class_name": ["Test Class"],
                "due_date": [pd.Timestamp(year=2022, month=12, day=31)]
            }
        )

    monkeypatch.setattr(ccemail, "_get_assignment_data", mock)


# Fixture for a test announcement email list
@pytest.fixture
def announcement_email_list(student_emails, student_names):
    msg_queue = []
    for i in range(3):
        msg = EmailMessage()
        msg["Subject"] = "[Test Class] New Announcement"
        msg["From"] = ccemail.CC_EMAIL_ADDR
        msg["To"] = Address(student_names[i], f"student{i + 1}", "domain")
        msg.set_content(ccemail._ANNOUNCEMENT_HTML.format(
            student_name=student_names[i],
            class_name="Test Class",
            body="Test Announcement"
        ), subtype="html")
        msg_queue.append(msg)
    yield _serialize_messages(msg_queue)


# Fixture for a test assignment email list
@pytest.fixture
def assignment_email_list(student_emails, student_names):
    msg_queue = []
    for i in range(3):
        msg = EmailMessage()
        msg["Subject"] = "[Test Class] Assignment Created - Test Assignment"
        msg["From"] = ccemail.CC_EMAIL_ADDR
        msg["To"] = Address(student_names[i], f"student{i + 1}", "domain")
        msg.set_content(ccemail._ASSIGNMENT_HTML.format(
            student_name=student_names[i],
            class_name="Test Class",
            assignment_name="Test Assignment",
            due_date="December 31, 2022"
        ), subtype="html")
        msg_queue.append(msg)
    yield _serialize_messages(msg_queue)


# Fixture for a test grade email sent to a single student
@pytest.fixture
def grade_email_list_single_student(student_emails, student_names):
    msg = EmailMessage()
    msg["Subject"] = "[Test Class] Assignment Graded - Test Assignment"
    msg["From"] = ccemail.CC_EMAIL_ADDR
    msg["To"] = Address(student_names[0], f"student1", "domain")
    msg.set_content(ccemail._GRADE_HTML.format(
        student_name=student_names[0],
        class_name="Test Class",
        assignment_name="Test Assignment"
    ), subtype="html")
    yield _serialize_messages([msg])


# Fixture for a test grade email sent to an entire class
@pytest.fixture
def grade_email_list_class(student_emails, student_names):
    msg_queue = []
    for i in range(3):
        msg = EmailMessage()
        msg["Subject"] = "[Test Class] Assignment Graded - Test Assignment"
        msg["From"] = ccemail.CC_EMAIL_ADDR
        msg["To"] = Address(student_names[i], f"student{i + 1}", "domain")
        msg.set_content(ccemail._GRADE_HTML.format(
            student_name=student_names[i],
            class_name="Test Class",
            assignment_name="Test Assignment"
        ), subtype="html")
        msg_queue.append(msg)
    yield _serialize_messages(msg_queue)


@pytest.fixture
def submission_email_list(student_emails, student_names):
    msg = EmailMessage()
    msg["Subject"] = "[Test Class] Submission Received - Test Assignment"
    msg["From"] = ccemail.CC_EMAIL_ADDR
    msg["To"] = Address(student_names[0], f"student1", "domain")
    msg.set_content(ccemail._SUBMISSION_HTML.format(
        student_name=student_names[0],
        class_name="Test Class",
        assignment_name="Test Assignment"
    ), subtype="html")
    yield _serialize_messages([msg])


# Test announcement email
def test_send_announcement(mock_get_class_emails, announcement_email_list):
    msg_queue = ccemail.send_announcement("Test Class", "Test Announcement")
    msg_queue = _serialize_messages(msg_queue)
    assert msg_queue == announcement_email_list


# Test assignment email
def test_send_assignment(mock_get_class_emails, mock_get_assignment_data,
                         assignment_email_list):
    msg_queue = ccemail.send_assignment(1)
    msg_queue = _serialize_messages(msg_queue)
    assert msg_queue == assignment_email_list


# Test grade email (single student)
def test_send_grades_single_student(mock_get_class_emails, mock_get_assignment_data,
                                    grade_email_list_single_student):
    msg_queue = ccemail.send_grades(1, 1)
    msg_queue = _serialize_messages(msg_queue)
    assert msg_queue == grade_email_list_single_student


# Test grade email (entire class)
def test_send_grades_class(mock_get_class_emails, mock_get_assignment_data,
                           grade_email_list_class):
    msg_queue = ccemail.send_grades(1)
    msg_queue = _serialize_messages(msg_queue)
    assert msg_queue == grade_email_list_class


# Test assignment submission email
def test_send_submission(mock_get_class_emails, mock_get_assignment_data,
                         submission_email_list):
    msg_queue = ccemail.send_submission(1, 1)
    msg_queue = _serialize_messages(msg_queue)
    assert msg_queue == submission_email_list
