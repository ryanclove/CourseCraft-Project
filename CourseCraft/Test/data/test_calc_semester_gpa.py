import pandas as pd
import pytest

from web.app import student


# Calc Semester GPA only tests the calculation, not the validity of inputs.


# Test a freshman with 0 credits, he assumes he'll get a 4.0 in each class, so his semester gpa should calc to 4.0
def test_freshman_gpa_4():
    likely_grade = [4, 4, 4, 4]
    course_credits = [4, 4, 4, 4]

    grades = pd.DataFrame()
    grades['likely_grade'] = likely_grade
    grades['course_credits'] = course_credits
    test = student.calculate_semester_gpa_method(grades, 0, 0)
    assert test == 4


# Test a freshman with 0 credits, he assumes he'll get a 0.0 in each class, so his semester gpa should calc to 0.0
def test_freshman_gpa_0():
    likely_grade = [0, 0, 0, 0]
    course_credits = [4, 4, 4, 4]

    grades = pd.DataFrame()
    grades['likely_grade'] = likely_grade
    grades['course_credits'] = course_credits
    test = student.calculate_semester_gpa_method(grades, 0, 0)
    assert test == 0


# Test a freshman with 0 credits, he assumes he'll get a 4.0 and 2.0 in alternating class, so his semester gpa should
# calc to 3.0
def test_freshman_gpa_3():
    likely_grade = [4, 2, 4, 2]
    course_credits = [4, 4, 4, 4]

    grades = pd.DataFrame()
    grades['likely_grade'] = likely_grade
    grades['course_credits'] = course_credits
    test = student.calculate_semester_gpa_method(grades, 0, 0)
    assert test == 3


# Test a student with 12 credits and 3.0 gpa, he assumes in 12 credits this semester he'll get all 4.0, should calc
# to 3.5
def test_student_gpa_1():
    likely_grade = [4, 4, 4]
    course_credits = [4, 4, 4]

    grades = pd.DataFrame()
    grades['likely_grade'] = likely_grade
    grades['course_credits'] = course_credits
    test = student.calculate_semester_gpa_method(grades, 3, 12)
    assert test == 3.5


# Test a student with 12 credits and 0.0 gpa, he assumes in 12 credits this semester he'll get all 4.0, should calc
# to 2.0
def test_student_gpa_2():
    likely_grade = [4, 4, 4]
    course_credits = [4, 4, 4]

    grades = pd.DataFrame()
    grades['likely_grade'] = likely_grade
    grades['course_credits'] = course_credits
    test = student.calculate_semester_gpa_method(grades, 0, 12)
    assert test == 2.0


# Test a student with 12 credits and 4.0 gpa, he assumes in 12 credits this semester he'll get all 4.0, should calc
# to 4.0
def test_student_gpa_3():
    likely_grade = [4, 4, 4]
    course_credits = [4, 4, 4]

    grades = pd.DataFrame()
    grades['likely_grade'] = likely_grade
    grades['course_credits'] = course_credits
    test = student.calculate_semester_gpa_method(grades, 4, 12)
    assert test == 4.0


# Test a student who is taking 0 credit courses and with a 4.0 GPA, his semester GPA should remain the same at 4.0
def test_student_gpa_4():
    likely_grade = [4, 4, 4]
    course_credits = [0, 0, 0]

    grades = pd.DataFrame()
    grades['likely_grade'] = likely_grade
    grades['course_credits'] = course_credits
    test = student.calculate_semester_gpa_method(grades, 4, 12)
    assert test == 4.0
