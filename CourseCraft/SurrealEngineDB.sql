CREATE DATABASE IF NOT EXISTS SurrealEngine;

USE SurrealEngine;


CREATE TABLE users (
  id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
  email VARCHAR(320),
  full_name VARCHAR(70),
  user_password VARCHAR(70),
  role ENUM('student','professor','dean')
  );

CREATE TABLE professors (
  professors_id INT PRIMARY KEY REFERENCES users (id)
);

CREATE TABLE students (
  students_id int PRIMARY KEY REFERENCES users (id),
  major ENUM('CS','Math','Biology','Physics','Chemistry','English'),
  gpa DOUBLE,
  credits_earned DOUBLE,
  credits_taking DOUBLE,
  gpa_credits DOUBLE
);

CREATE TABLE dean (
  deans_id int PRIMARY KEY REFERENCES users (id)
);

CREATE TABLE classes (
  class_name VARCHAR(70) PRIMARY KEY,
  major Enum('CS','Math','Biology','Physics','Chemistry','English'),
  classTime_start_date DATE,
  classTime_end_date DATE,
  classTime_days_of_week ENUM('Monday','Tuesday','Wednesday','Thursday','Friday','Mon/Wed','Tue/Thu'),
  classTime_start_time TIME,
  classTime_end_time TIME
);

CREATE TABLE enrolled (
  enrolled_student_id int REFERENCES students (students_id),
  enrolled_class_name VARCHAR(70) REFERENCES classes (class_name),
  PRIMARY KEY (enrolled_student_id, enrolled_class_name)
);

CREATE TABLE teaches (
  teacher_professor_id int REFERENCES professors (professors_id),
  teaches_class_name VARCHAR(70) REFERENCES classes (class_name),
  PRIMARY KEY (teacher_professor_id, teaches_class_name)
);

CREATE TABLE Assignments (
  assignment_name VARCHAR(70) PRIMARY KEY,
  file_name VARCHAR(255),
  class_name VARCHAR(70) REFERENCES classes (class_name)
  due_date DATE,
);

CREATE TABLE grades (
  grades_assignment_id int PRIMARY KEY REFERENCES courseAssingments (assignment_id),
  grades_student_id int REFERENCES students (student_id),
  grade DOUBLE 
);

CREATE TABLE announcements (
  announcement_id int PRIMARY KEY AUTO_INCREMENT,
  announcement_subject VARCHAR(150),
  announcement_text TEXT(65532),
  announcements_class_name VARCHAR(70) REFERENCES classes (class_name)
);

