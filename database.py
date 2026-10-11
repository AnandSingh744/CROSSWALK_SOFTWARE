import sqlite3
from pathlib import Path
import pandas as pd

BASE_DIR=Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "crosswalk.db"

def get_connection():
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def create_tables(conn):

    cursor = conn.cursor()

    # -----------------------------
    # Users
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            User_Id TEXT PRIMARY KEY,
            Name TEXT NOT NULL,
            Email TEXT NOT NULL UNIQUE,
            Password_Hash TEXT NOT NULL,
            Role TEXT NOT NULL
        )
    """)

    # -----------------------------
    # Students
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            Student_Id TEXT PRIMARY KEY,
            User_Id TEXT NOT NULL,
            Degree TEXT,
            Course TEXT,
            Specialization TEXT,
            College TEXT,
            Technical_Skills TEXT,
            Soft_Skills TEXT,
            Certifications TEXT,
            Areas_Of_Interest TEXT,
            Preferred_Industries TEXT,
            Career_Preferences TEXT,
            Profile_Status TEXT,

            FOREIGN KEY (User_Id)
                REFERENCES users(User_Id)
        )
    """)

    # -----------------------------
    # Education
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS education (
            Education_Id TEXT PRIMARY KEY,
            Degree TEXT,
            Course TEXT,
            Specialization TEXT,
            College TEXT
        )
    """)

    # -----------------------------
    # Skills
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS skills (
            Skill_Id TEXT PRIMARY KEY,
            Skill_Name TEXT NOT NULL,
            Category TEXT,
            Domain TEXT,
            Demand_Trend TEXT
        )
    """)

    # -----------------------------
    # Careers
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS careers (
            Career_Id TEXT PRIMARY KEY,
            Career_Name TEXT NOT NULL,
            Industry TEXT,
            Min_Education_Level TEXT,
            Required_Degrees TEXT,
            Preferred_Courses TEXT,
            Preferred_Specializations TEXT,
            Related_Interest_Areas TEXT,
            Short_Description TEXT
        )
    """)

    # -----------------------------
    # Career Skills
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS career_skills (
            Career_Id TEXT NOT NULL,
            Skill_Id TEXT NOT NULL,
            Requirement_Type TEXT,

            PRIMARY KEY (Career_Id, Skill_Id),

            FOREIGN KEY (Career_Id)
                REFERENCES careers(Career_Id),

            FOREIGN KEY (Skill_Id)
                REFERENCES skills(Skill_Id)
        )
    """)

    # -----------------------------
    # Courses
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            Course_Id TEXT PRIMARY KEY,
            Course_Name TEXT NOT NULL,
            Skills_Covered TEXT,
            Level TEXT,
            Duration_Weeks INTEGER
        )
    """)

    # -----------------------------
    # Curriculum
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS curriculum (
            Subject_Id TEXT PRIMARY KEY,
            Subject_Name TEXT NOT NULL,
            Degree TEXT,
            Course TEXT,
            Semester INTEGER,
            Credits INTEGER,
            Subject_Type TEXT,
            Skills_Taught TEXT
        )
    """)

    # -----------------------------
    # Employment
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS employment (
            Occupation_Id TEXT PRIMARY KEY,
            Job_Title TEXT,
            Industry TEXT,
            Degree TEXT,
            Course TEXT,
            Specialization TEXT,
            College TEXT,
            Graduation_Year INTEGER,
            Employment_Status TEXT,
            Experience_Level TEXT,
            Previous_Job_Title TEXT
        )
    """)

    # -----------------------------
    # Label mappings
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS label_mappings (
            Mapping_Id TEXT PRIMARY KEY,
            Label_Type TEXT,
            Raw_Label TEXT,
            Standard_Label TEXT
        )
    """)

    # -----------------------------
    # Data quality tests
    # -----------------------------
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_quality_test (
            Test_Id TEXT PRIMARY KEY,
            Category TEXT,
            Module TEXT,
            Target_Dataset TEXT,
            Input_Record TEXT,
            Issue_Description TEXT,
            Expected_System_Behavior TEXT,
            Review_Log_Expected TEXT,
            Match_Confidence REAL
        )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS standardized_education (
        Education_Id TEXT PRIMARY KEY,
        Degree TEXT,
        Course TEXT,
        Specialization TEXT,
        College TEXT
    )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS standardized_employment (
            Occupation_Id TEXT PRIMARY KEY,
            Job_Title TEXT,
            Industry TEXT,
            Degree TEXT,
            Course TEXT,
            Specialization TEXT,
            College TEXT,
            Graduation_Year INTEGER,
            Employment_Status TEXT,
            Experience_Level TEXT,
            Previous_Job_Title TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS standardized_skills (
            Skill_Id TEXT PRIMARY KEY,
            Skill_Name TEXT,
            Category TEXT,
            Domain TEXT,
            Demand_Trend TEXT
        )
    """)

    conn.commit()

def import_csv(conn, filename, table_name):
    """Import a CSV file into a SQLite table."""

    file_path = DATA_DIR / filename

    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {file_path}"
        )

    df = pd.read_csv(file_path)

    df.to_sql(
        table_name,
        conn,
        if_exists="append",
        index=False
    )

    print(
        f"Imported {len(df)} rows "
        f"from {filename} -> {table_name}"
    )

def initialize_database():

    conn = get_connection()

    try:
        create_tables(conn)

        datasets = [
            ("users.csv", "users"),
            ("students.csv", "students"),
            ("education.csv", "education"),
            ("skills.csv", "skills"),
            ("careers.csv", "careers"),
            ("career_skills.csv", "career_skills"),
            ("courses.csv", "courses"),
            ("curriculum.csv", "curriculum"),
            ("employment.csv", "employment"),
            ("label_mappings.csv", "label_mappings"),
            ("data_quality_test.csv", "data_quality_test"),
        ]

        for filename, table_name in datasets:
            import_csv(conn, filename, table_name)

        print("\nDatabase initialized successfully.")

    finally:
        conn.close()

if __name__ == "__main__":
    initialize_database()