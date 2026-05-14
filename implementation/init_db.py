import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("lab.db")

SCHEMA_SQL = """
DROP TABLE IF EXISTS enrollments;
DROP TABLE IF EXISTS courses;
DROP TABLE IF EXISTS students;

CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    cohort TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    score REAL NOT NULL CHECK (score >= 0 AND score <= 100)
);

CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    department TEXT NOT NULL
);

CREATE TABLE enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL REFERENCES students(id),
    course_id INTEGER NOT NULL REFERENCES courses(id),
    grade REAL NOT NULL CHECK (grade >= 0 AND grade <= 100),
    UNIQUE(student_id, course_id)
);
"""

SEED_SQL = """
INSERT INTO students (name, cohort, email, score) VALUES
    ('An Nguyen', 'A1', 'an.nguyen@example.edu', 88.5),
    ('Binh Tran', 'A1', 'binh.tran@example.edu', 91.0),
    ('Chi Le', 'B2', 'chi.le@example.edu', 76.25),
    ('Dung Pham', 'B2', 'dung.pham@example.edu', 84.75),
    ('Evan Vo', 'C3', 'evan.vo@example.edu', 69.5);

INSERT INTO courses (title, department) VALUES
    ('Introduction to MCP', 'AI'),
    ('SQLite Fundamentals', 'Data'),
    ('Applied Python', 'Engineering');

INSERT INTO enrollments (student_id, course_id, grade) VALUES
    (1, 1, 90.0),
    (1, 2, 87.0),
    (2, 1, 92.5),
    (3, 2, 78.0),
    (4, 3, 86.0),
    (5, 3, 71.0);
"""


def create_database(db_path: str | Path = DB_PATH) -> Path:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA_SQL)
        connection.executescript(SEED_SQL)
        connection.commit()

    return path


if __name__ == "__main__":
    created_path = create_database()
    print(f"Initialized SQLite database at {created_path}")
