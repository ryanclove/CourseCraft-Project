from functools import partial
from typing import Dict, Union

import dash_bootstrap_components as dbc

from web.data.user import Student, Professor
from web.data.dbconnector import DBConnector
from web.data.user import Student

CCDB = DBConnector()

# All navbars share these properties
navbar_template = partial(
    dbc.NavbarSimple,
    brand="CourseCraft",
    color="dark",
    dark=True,
)

# Login navbar
login_navbar = navbar_template([])


# Dynamically generate the student navbar using user session data.
# Accepts either a Student object or the Student dict stored in the session.
def student_navbar(account: Union[Student, Dict]) -> dbc.NavbarSimple:
    if isinstance(account, Student):
        account = account.__dict__

    df_courses = CCDB.get_enrolled_course(account['id'])
    courses = [row.enrolled_class_name for row in df_courses.itertuples()]
    course_mgmt_dropdown = dbc.DropdownMenu(
        [dbc.DropdownMenuItem(c, href=f"/lecture/{c}") for c in courses],
        label="Course Management"
    )
    return navbar_template(
        children=[
            dbc.DropdownMenu(
                [
                    dbc.DropdownMenuItem(
                        "Register for a Class", href="course_registration"
                    ),
                    dbc.DropdownMenuItem(
                        "View Schedule", href="/view_schedule"
                    )
                ],
                label="Course Registration"
            ),
            course_mgmt_dropdown,
            dbc.DropdownMenu(
                [
                    dbc.DropdownMenuItem(
                        "Calculate GPA after this semester", href="/generate_semester_gpa"
                    ),
                    dbc.DropdownMenuItem(
                        "Calculate Potential GPA", href="/generate_future_gpa"
                    )
                ],
                label="Degree Navigator"
            )
        ],
        brand_href="/"
    )


# Dynamically generate professor navbar.
def professor_navbar(account: Union[Professor, Dict]) -> dbc.NavbarSimple:
    if isinstance(account, Professor):
        account = account.__dict__
    df_courses = CCDB.find_courses_taught(account)
    prof_courses = [row.class_name for row in df_courses.itertuples()]
    course_mgmt_dropdown = dbc.DropdownMenu(
        [dbc.DropdownMenuItem(c, href=f"/prof-lecture/{c}") for c in prof_courses],
        label="Course Management"
    )
    return navbar_template(
        children=[
            dbc.DropdownMenu(
                [
                    dbc.DropdownMenuItem(
                        "Register to Teach a Class", href="/register_to_teach"
                    )
                ],
                label="Course Registration"
            ),
            course_mgmt_dropdown,
        ],
        brand_href="/"
    )


# Dynamically generates dean navbar.
dean_navbar = navbar_template(
    children=[
        dbc.DropdownMenu(
            [
                dbc.DropdownMenuItem(
                    children="Create New Course", href="create_course"
                )
            ],
            label="Course Registration"
        )
    ],
    brand_href="/"
)
