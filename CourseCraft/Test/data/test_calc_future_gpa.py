import pytest

from web.app import student


# Calc Future GPA only tests the calculation, not the validity of inputs.


# Test a freshman with 0 credits, he wants a 4.0, he'll need to average a 4.0 over any amount of credits.
def test_freshman_gpa_4():
    test = student.calculate_future_gpa_method(0, 0, 15, 4.0)
    assert test == 4.0


# Test a freshman with 0 credits, he wants a 0 GPA over 15 creds, he'll need to average a 0.0 over those credits.
def test_freshman_gpa_0():
    test = student.calculate_future_gpa_method(0, 0, 15, 0)
    assert test == 0


# Test a student who has a 4.0 with 15 credits, what he needs to get a 3.5 over 15 credits. He would need a 3.0
def test_student_gpa_35():
    test = student.calculate_future_gpa_method(4.0, 15, 15, 3.5)
    assert test == 3.0


# Test to show that we can get a 0 gpa from a 4.0 student with 15 credits, but the result should be negative which is
# impossible
def test_student_gpa_0_neg():
    test = student.calculate_future_gpa_method(4.0, 15, 15, 0)
    assert test < 0


# Test to show that we can get a 4.5 gpa from a 4.0 student with 15 credits, but the result should be greater than 4.0
# which is impossible.
def test_student_gpa_40_greater():
    test = student.calculate_future_gpa_method(4.0, 15, 15, 4.5)
    assert test > 4
