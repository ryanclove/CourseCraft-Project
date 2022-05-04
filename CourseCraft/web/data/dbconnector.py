from typing import Dict, Optional, Union

import pandas as pd
import sqlalchemy
from sqlalchemy import Table, MetaData, insert
from sqlalchemy import text

from web.data.user import UserType, User, Student, Dean, Professor, Major

_DB_CONN_STR = "mariadb+pymysql://test:12345abc@cs431-11.cs.rutgers.edu:3306/SurrealEngine"

_SEL_USER_QRY = (
    "select * "
    "from {user_type}s t "
    "join users u on (t.{user_type}s_id = u.id) "
    "where u.email='{email}' and u.user_password='{password}' and u.role='{user_type}'"
)

_SEL_EMAIL_QRY = (
    "select * "
    "from users u "
    "where u.email in ("
    "   select u2.email "
    "   from users u2 "
    "   where u2.email='{email}'"
    ")"
)

_INSERT_USER_QRY = (
    "insert into users "
    "(email, full_name, user_password, role) "
    "values('{email}', '{name}', '{password}', '{user_type}'); "
)

_INSERT_STUDENT_QRY = (
    "insert into students "
    "(students_id, major) "
    "values({id}, '{major}');"
)

_INSERT_PROFESSOR_QRY = (
    "insert into professors "
    "(professors_id) "
    "values({id});"
)

_INSERT_DEAN_QRY = (
    "insert into deans "
    "(deans_id) "
    "values({id});"
)

_SEL_COURSE_ENROLLMENT_QRY = (
    "select * "
    "from enrolled e "
    "join students s on (e.enrolled_student_id = s.students_id) "
    "join users u on (s.students_id = u.id) "
    "where e.enrolled_class_name='{class_name}'"
)

_SEL_COURSE_PROF_QRY = (
    "select * "
    "from teaches t "
    "join professors p on (t.teacher_professor_id = p.professors_id) "
    "join users u on (p.professors_id = u.id) "
    "where t.teaches_class_name='{class_name}'"
)

_SEL_COUR_TOUGHT_QRY = {
    "select class_name "
    "from classes"
    "inner join  "
}

_SEL_ASSIGNMENT_QRY = (
    "select * "
    "from assignments a "
    "where a.assignment_id='{assignment_id}'"
)


# Build a Student class from a database row
def _build_student(row) -> Student:
    return Student(
        id=row["students_id"],
        email=row["email"],
        password=row["user_password"],
        name=row["full_name"],
        major=row["major"],
        gpa=row["gpa"],
        credits_earned=row["credits_earned"],
        credits_taking=row["credits_taking"],
        gpa_credits=row["gpa_credits"]
    )


# Build a Professor class from a database row
def _build_professor(row) -> Professor:
    return Professor(
        id=row["professors_id"],
        email=row["email"],
        password=row["user_password"],
        name=row["full_name"]
    )


# Build a Dean class from a database row
def _build_dean(row) -> Dean:
    return Dean(
        id=row["id"],
        email=row["email"],
        password=row["user_password"],
        name=row["full_name"]
    )


# Connect the software to our virtual machine database
class DBConnector:

    def __init__(self):
        self._engine = sqlalchemy.create_engine(_DB_CONN_STR)

    # Execute a select query and return the results as either a pandas DataFrame or a dict
    def _execute_select(self, query: str, as_dict: bool = False) -> Union[pd.DataFrame, Dict]:
        df_result = pd.read_sql(query, self._engine)
        if as_dict:
            return df_result.to_dict("index")
        return df_result

    # Execute an insert query
    def _execute_insert(self, query: str) -> None:
        with self._engine.connect() as conn:
            conn.execute(text(query))

    # Return the login info of a certain user type with the given email/password.
    # Given how the database is set up, this should return only one user.
    # Return None if no such user exists.
    def find_user(self, email: str, password: str, user_type: Union[UserType, str]) -> Optional[User]:
        query = _SEL_USER_QRY.format(
            email=email,
            password=password,
            user_type=user_type.name.lower()
        )
        df_result = self._execute_select(query)

        if df_result.empty:
            return None
        df_result = df_result.iloc[0]

        if user_type == UserType.STUDENT:
            return _build_student(df_result)
        elif user_type == UserType.PROFESSOR:
            return _build_professor(df_result)
        elif user_type == UserType.DEAN:
            return _build_dean(df_result)
        else:
            return None

    # Create a new user if the selected email isn't taken by another user.
    # Return True/False based on whether the insert was successful.
    def create_user(self,
                    email: str,
                    password: str,
                    user_type: Union[UserType, str],
                    name: str,
                    major: Optional[str] = None) -> bool:
        # Validate input
        if isinstance(user_type, UserType):
            user_type = user_type.name
        user_type = user_type.lower()
        if user_type == "student" and major is None:
            raise ValueError("A student account requires a major")
        # Check that email does not exist
        email_query = _SEL_EMAIL_QRY.format(email=email)
        df_accounts = self._execute_select(email_query)
        if not df_accounts.empty:
            return False
        # Insert new user into users table
        insert_user_query = _INSERT_USER_QRY.format(
            email=email,
            name=name,
            password=password,
            user_type=user_type
        )
        self._execute_insert(insert_user_query)
        # Insert new user into its respective role table
        new_id = self._execute_select(email_query).iloc[0]["id"]
        if user_type == "student":
            insert_role_query = _INSERT_STUDENT_QRY.format(id=new_id, major=major)
        elif user_type == "professor":
            insert_role_query = _INSERT_PROFESSOR_QRY.format(id=new_id)
        else:  # dean
            insert_role_query = _INSERT_DEAN_QRY.format(id=new_id)
        self._execute_insert(insert_role_query)
        return True

    # Create a class as a dean
    # creates a class in the database with start and end dates, start and end times, and the weekdays the class meets
    def create_class(self, name, major, meeting_days, start_date, end_date, start_time, end_time):
        query = f"INSERT INTO classes (class_name, major, classTime_days_of_week, classTime_start_date, classTime_end_date, " \
                f"classTime_start_time, classTime_end_time) VALUES ('{name}', '{major}', '{meeting_days}', '{start_date}'," \
                f"'{end_date}', '{start_time}', '{end_time}' )"
        with self._engine.connect() as conn:
            return conn.execute(text(query))

    # register to teach a class as a professor.
    # creates a connection to the database, creates a table for teaches
    # insert into the teaches table a copy of the class name and teacher professor id using session info.
    def teach_class(self, account, class_name):
        myEngine = self._engine
        metaData = MetaData(bind=myEngine)
        teaches = Table(
            "teaches",
            metaData,
            autoload_with=myEngine
        )
        stmt = insert(teaches).values(teaches_class_name=class_name, teacher_professor_id=account)
        myEngine.execute(stmt)

    # read the database for classes with no teachers
    def find_empty_classes(self):
        query = (
            "select * "
            "from classes c "
            "where c.class_name not in ("
            "   select t.teaches_class_name "
            "   from teaches t "
            ")"
        )
        df_result = pd.read_sql(query, self._engine)
        return df_result

    # Get all the courses the professor teaches.
    def find_courses_taught(self, account):
        query = f"select class_name from classes inner join teaches on classes.class_name = " \
                f"teaches.teaches_class_name where teaches.teacher_professor_id={account['id']}"
        df_result = pd.read_sql(query, self._engine)
        return df_result

    # Returns a df result of all available classes from classes table
    # query only returns classes that the current student is not enrolled in
    def get_available_classes(self, id):
        # query = "SELECT * FROM classes"
        query = f"select * from classes c where c.class_name not in " \
                f"(select enrolled_class_name from enrolled where enrolled_student_id = {id});"

        result = pd.read_sql(query, self._engine)
        if result.empty:
            return None
        else:
            return result

    # Return list of classes student is already enrolled in
    def get_enrolled_course(self, student_id):
        check_enrollment_query = f"SELECT * FROM enrolled WHERE enrolled_student_id = '{student_id}';"
        enrolled_classes = self._execute_select(check_enrollment_query)
        return enrolled_classes

    # Return a DataFrame containing data for all students enrolled in a class
    def get_course_enrollment(self, class_name: str) -> pd.DataFrame:
        query = _SEL_COURSE_ENROLLMENT_QRY.format(
            class_name=class_name
        )
        return self._execute_select(query)

    # Return a course's professor. If not taught by anyone, return an empty DataFrame
    def get_course_professor(self, class_name: str) -> pd.DataFrame:
        query = _SEL_COURSE_PROF_QRY.format(
            class_name=class_name
        )
        return self._execute_select(query)

    # Handles course registration
    def course_registration(self, classes, student_id):
        query = f"INSERT INTO enrolled (enrolled_student_id, enrolled_class_name) VALUES "

        for course in classes:
            if course != classes[-1]:
                query = query + f"('{student_id}', '{course}'), "
            else:
                query = query + f"('{student_id}', '{course}');"

        self._execute_insert(query)

    # Returns class info (name, date, time, etc) for the surrent students schedule
    def get_course_schedule(self, student_id):
        query = f"select * from classes c where c.class_name in " \
                f"(select enrolled_class_name from enrolled where enrolled_student_id = {student_id})" \
                f" order by field(classTime_days_of_week, 'Monday', 'Tuesday')ASC, classTime_start_time ASC;"

        result = pd.read_sql(query, self._engine)
        return result

    # Returns a df schedule of courses for the given day and student
    def get_daily_schedule(self, student_id, day):
        query = f"select * from classes c where c.classTime_days_of_week='{day}' and c.class_name  in " \
                f"(select enrolled_class_name from enrolled where enrolled_student_id = {student_id});"

        result = pd.read_sql(query, self._engine)
        return result

    # Returns a df schedule of courses for the given two-day courses (mon/wed, tue/thu)
    def get_two_day_schedule(self, student_id, days):
        query = f"select * from classes c where c.classTime_days_of_week='{days}' and c.class_name  in " \
                f"(select enrolled_class_name from enrolled where enrolled_student_id = {student_id});"

        result = pd.read_sql(query, self._engine)
        return result

    # Get all assignment fields from its assignment ID
    def get_assignment_data(self, assignment_id: int) -> pd.DataFrame:
        query = _SEL_ASSIGNMENT_QRY.format(
            assignment_id=assignment_id
        )
        return self._execute_select(query)

    # Get all assignments for a particular course
    def get_assignments(self, lecture):
        query = f"SELECT assignment_id, assignment_name, file_name, due_date FROM assignments WHERE class_name ='{lecture}'"
        return pd.read_sql(query, self._engine)

    # Used by student role to sumbit an assignment
    # Enters a specific students uploaded assignment's filename into the database
    def submit_assignments(self, assignment_id, student_id, file_name):
        with self._engine.connect() as conn:
            try:
                query = f"INSERT INTO grades (assignment_id, student_id, submitted_file) VALUES ({assignment_id}, {student_id}, '{file_name}') "
                result = conn.execute(text(query))
            except Exception:
                query = f"UPDATE grades SET submitted_file='{file_name}' WHERE assignment_id={assignment_id} and student_id={student_id}"
                result = conn.execute(text(query))
            return result

    # Used by professors to create assignments that will be stored in the DB
    def create_assignments(self, assignment_name, file_name, class_name, due_date):
        query = f"INSERT INTO assignments (assignment_name, file_name, class_name, due_date) VALUES " \
                f"('{assignment_name}', '{file_name}', '{class_name}','{due_date}')"
        self._execute_insert(query)

    # Used by professors to update submitted assignments with their inputted grade
    def grade_assignments(self, assignment_id, student_id, submitted_file, grade):
        query = f"UPDATE grades " \
                f"SET grade = {grade} " \
                f"WHERE " \
                f"assignment_id = {assignment_id} AND " \
                f"student_id = {student_id} AND " \
                f"submitted_file = '{submitted_file}'"
        self._execute_insert(query)

    # Used by Professors to see the list of submissions by students for an assignment
    def get_grades(self, assignment_id):
        query = f"SELECT assignment_id, student_id, submitted_file, grade FROM grades WHERE assignment_id ='{assignment_id}'"
        return pd.read_sql(query, self._engine)

    # Used by Students to see the list of graded assignments for that student
    def get_my_grades(self, student_id, lecture):
        query = f"SELECT g.assignment_id, g.student_id, g.submitted_file, g.grade, a.assignment_name FROM grades g, assignments a " \
                f" WHERE student_id ='{student_id}'" \
                f" AND g.assignment_id = a.assignment_id" \
                f" AND a.class_name = '{lecture}'"
        return pd.read_sql(query, self._engine)

    # Used by email server to retrieve announcement details
    def get_announcement(self, announcements_class_name):
        query = f"SELECT announcement_id, announcement_subject, announcement_text, announcements_class_name " \
                f"FROM announcements WHERE announcements_class_name ='{announcements_class_name}'"
        return pd.read_sql(query, self._engine)

    # Used by professors to create an announcement to be store in the DB
    def create_announcement(self, announcement_subject, announcement_text, class_name):
        query = f"INSERT INTO announcements (announcement_subject, announcement_text, announcements_class_name) VALUES " \
                f"('{announcement_subject}', '{announcement_text}', '{class_name}')"
        self._execute_insert(query)
