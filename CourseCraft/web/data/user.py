from enum import Enum


# class for role type
class UserType(Enum):
    STUDENT = 0
    PROFESSOR = 1
    DEAN = 2


# class representing all selectable majors
class Major(Enum):
    CS = 0
    MATH = 1
    BIOLOGY = 2
    PHYSICS = 3
    CHEMISTRY = 4
    ENGLISH = 5


# Represents a record in the USERS table
class User:
    def __init__(self, id: int, email: str, password: str, name: str):
        self.id = id
        self.email = email
        self.password = password
        self.name = name


# Represents a record in the STUDENTS table
class Student(User):
    def __init__(self, id: int, email: str, password: str, name: str,
                 major: str, gpa: float, credits_earned: float,
                 credits_taking: float, gpa_credits: float):
        super().__init__(id, email, password, name)
        self.major = major
        self.gpa = gpa
        self.credits_earned = credits_earned
        self.credits_taking = credits_taking
        self.gpa_credits = gpa_credits


# Represents a record in the PROFESSOR table
class Professor(User):
    def __init__(self, id: int, email: str, password: str, name: str, ):
        super().__init__(id, email, password, name)


# Represents a record in the DEAN table
class Dean(User):
    def __init__(self, id: int, email: str, password: str, name: str, ):
        super().__init__(id, email, password, name)
