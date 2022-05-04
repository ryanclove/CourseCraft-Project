import smtplib
from email.headerregistry import Address
from email.message import EmailMessage
from typing import List, Optional, Union

import pandas as pd

from web.data.dbconnector import DBConnector

CCDB = DBConnector()

# Announcement template
_ANNOUNCEMENT_HTML = """\
        <html>
            <head></head>
            <body>
                <p>Hello {student_name},</p>
                <p>You have an announcement from your course <b>{class_name}</b>:</p>
                <p>{body}</p>
            </body>
        </html>
        """

# Assignment template
_ASSIGNMENT_HTML = """\
        <html>
            <head></head>
            <body>
                <p>Hello {student_name},</p>
                <p>You have a new assignment from your course <b>{class_name}</b>:</p>
                <p><b>{assignment_name}<br>Due Date: {due_date}</b></p>
            </body>
        </html>
        """

# Grade notification template
_GRADE_HTML = """
        <html>
            <head></head>
            <body>
                <p>Hello {student_name},</p>
                <p>You have a grade update for the following assignment:</p>
                <p><b>{class_name}<br>{assignment_name}</b></p>
                <p>Please login to CourseCraft to view your grade.</p>
            </body>
        </html>
        """

# Submission notification template
_SUBMISSION_HTML = """\
        <html>
            <head></head>
            <body>
                <p>Hello {student_name},</p>
                <p>We have received your submission for the following assignment:</p>
                <p><b>{class_name}<br>{assignment_name}</b></p>
                <p>You will be notified when your submission is graded.</p>
            </body>
        </html>
"""

# Static email address for all CourseCraft emails
CC_EMAIL_ADDR = "coursecraft.server@gmail.com"
CC_EMAIL_PWD = "coursecraft?server?"


# Decorator for sending a list of EmailMessage objects over the CourseCraft server
# This ensures we use only one SMTP connection per batch of emails
def mail_sender(f):
    def wrapper(*args, **kwargs):
        msg_queue = f(*args, **kwargs)
        with smtplib.SMTP("smtp.gmail.com", 587) as s:
            s.starttls()
            s.login(CC_EMAIL_ADDR, CC_EMAIL_PWD)
            for msg in msg_queue:
                s.send_message(msg)
        return msg_queue

    return wrapper


# Helper method to fetch the names and emails of all students
def _get_class_emails(class_name: str) -> pd.DataFrame:
    df_emails = CCDB.get_course_enrollment(class_name)
    df_emails = df_emails[["id", "email", "full_name"]]
    return df_emails


# Helper method to fetch an assignment's corresponding class
def _get_assignment_data(assignment_id: int) -> pd.DataFrame:
    return CCDB.get_assignment_data(assignment_id)


# Send an announcement to all students in a class
@mail_sender
def send_announcement(class_name: str, body: str, subject: Optional[str] = None) -> List[EmailMessage]:
    df_emails = _get_class_emails(class_name)
    msg_queue = []
    for row in df_emails.iterrows():
        # Set headers
        msg = EmailMessage()
        if subject:
            msg["Subject"] = f"[{class_name}] {subject}"
        else:
            msg["Subject"] = f"[{class_name}] New Announcement"
        msg["From"] = CC_EMAIL_ADDR
        # Create body
        student = row[1]  # strip index
        username, domain = student["email"].split("@")
        msg["To"] = Address(student["full_name"], username, domain)
        msg.set_content(_ANNOUNCEMENT_HTML.format(
            student_name=student["full_name"],
            class_name=class_name,
            body=body
        ), subtype="html")
        msg_queue.append(msg)
    return msg_queue


# Send an assignment notification to all students in a class
@mail_sender
def send_assignment(assignment_id: int) -> List[EmailMessage]:
    df_assignments = _get_assignment_data(assignment_id)
    asst_name, class_name, due_date = df_assignments.iloc[0][["assignment_name", "class_name", "due_date"]]
    due_date = due_date.to_pydatetime().strftime("%B %d, %Y")
    df_emails = _get_class_emails(class_name)
    msg_queue = []
    for row in df_emails.iterrows():
        # Set headers
        msg = EmailMessage()
        msg["Subject"] = f"[{class_name}] Assignment Created - {asst_name}"
        msg["From"] = CC_EMAIL_ADDR
        # Create body
        student = row[1]  # strip index
        username, domain = student["email"].split("@")
        msg["To"] = Address(student["full_name"], username, domain)
        msg.set_content(_ASSIGNMENT_HTML.format(
            student_name=student["full_name"],
            class_name=class_name,
            assignment_name=asst_name,
            due_date=due_date
        ), subtype="html")
        msg_queue.append(msg)
    return msg_queue


# Send a notification that an assignment grade has been updated
# This can be sent to an entire class or to one or more specified students
@mail_sender
def send_grades(assignment_id: int, student_ids: Optional[Union[List[int], int]] = None) -> List[EmailMessage]:
    df_assignments = _get_assignment_data(assignment_id)
    asst_name, class_name = df_assignments.iloc[0][["assignment_name", "class_name"]]
    df_emails = _get_class_emails(class_name)
    if student_ids:
        if isinstance(student_ids, int):
            student_ids = [student_ids]
        df_emails = df_emails[df_emails.id.isin(student_ids)]
    msg_queue = []
    for row in df_emails.iterrows():
        # Set headers
        msg = EmailMessage()
        msg["Subject"] = f"[{class_name}] Assignment Graded - {asst_name}"
        msg["From"] = CC_EMAIL_ADDR
        # Create body
        student = row[1]  # strip index
        username, domain = student["email"].split("@")
        msg["To"] = Address(student["full_name"], username, domain)
        msg.set_content(_GRADE_HTML.format(
            student_name=student["full_name"],
            class_name=class_name,
            assignment_name=asst_name
        ), subtype="html")
        msg_queue.append(msg)
    return msg_queue


# Send a notification that a student submitted an assignment
@mail_sender
def send_submission(assignment_id: int, student_id: int) -> List[EmailMessage]:
    df_assignments = _get_assignment_data(assignment_id)
    asst_name, class_name = df_assignments.iloc[0][["assignment_name", "class_name"]]
    df_emails = _get_class_emails(class_name)
    df_emails = df_emails[df_emails.id == student_id]
    student_email, student_name = df_emails.iloc[0][["email", "full_name"]]
    # Set headers
    msg = EmailMessage()
    msg["Subject"] = f"[{class_name}] Submission Received - {asst_name}"
    msg["From"] = CC_EMAIL_ADDR
    # Create body
    username, domain = student_email.split("@")
    msg["To"] = Address(student_name, username, domain)
    msg.set_content(_SUBMISSION_HTML.format(
        student_name=student_name,
        class_name=class_name,
        assignment_name=asst_name
    ), subtype="html")
    return [msg]  # return as List[EmailMessage] since that type is expected by @mail_sender
