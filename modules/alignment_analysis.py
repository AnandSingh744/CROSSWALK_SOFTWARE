from database import get_connection
from modules.career_exploration import retrieve_career_requirements


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def normalize(value):
    if value is None:
        return ""
    return str(value).strip().lower()


def split_values(value):
    if not value:
        return []

    return [
        item.strip()
        for item in str(value).split("|")
        if item.strip()
    ]


# ---------------------------------------------------------
# Get student profile
# ---------------------------------------------------------

def get_student_profile(student_id):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                Student_Id,
                Degree,
                Course,
                Specialization,
                Technical_Skills,
                Soft_Skills,
                Areas_Of_Interest,
                Preferred_Industries
            FROM students
            WHERE Student_Id = ?
        """, (student_id,))

        student = cursor.fetchone()

        if student is None:
            return None

        return {
            "Student_Id": student[0],
            "Degree": student[1],
            "Course": student[2],
            "Specialization": student[3],
            "Technical_Skills": split_values(student[4]),
            "Soft_Skills": split_values(student[5]),
            "Areas_Of_Interest": split_values(student[6]),
            "Preferred_Industries": split_values(student[7])
        }

    finally:
        conn.close()


# ---------------------------------------------------------
# Education Match
# ---------------------------------------------------------

def calculate_education_match(student, career):
    student_degree = normalize(student["Degree"])
    student_course = normalize(student["Course"])
    student_specialization = normalize(student["Specialization"])

    career_degree = normalize(career["Degree_Mapping"])
    career_course = normalize(career["Course"])
    career_specialization = normalize(career["Specialization"])

    degree_match = 1 if student_degree == career_degree else 0
    course_match = 1 if student_course == career_course else 0
    specialization_match = (
        1 if student_specialization == career_specialization else 0
    )

    education_score = (
        degree_match * 0.40
        + course_match * 0.30
        + specialization_match * 0.30
    )

    return {
        "degree_match": degree_match,
        "course_match": course_match,
        "specialization_match": specialization_match,
        "score": education_score
    }


# ---------------------------------------------------------
# Skill Match
# ---------------------------------------------------------

def calculate_skill_match(student, career):
    student_skills = set(
        normalize(skill)
        for skill in (
            student["Technical_Skills"]
            + student["Soft_Skills"]
        )
    )

    required_skills = career["Required_Skills"]

    if not required_skills:
        return {
            "matched_skills": [],
            "missing_skills": [],
            "score": 0
        }

    matched_skills = []
    missing_skills = []

    for skill in required_skills:
        if normalize(skill) in student_skills:
            matched_skills.append(skill)
        else:
            missing_skills.append(skill)

    score = len(matched_skills) / len(required_skills)

    return {
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "score": score
    }


# ---------------------------------------------------------
# Interest Match
# ---------------------------------------------------------

def calculate_interest_match(student, career):
    student_interests = set(
        normalize(item)
        for item in student["Areas_Of_Interest"]
    )

    preferred_industries = set(
        normalize(item)
        for item in student["Preferred_Industries"]
    )

    career_industry = normalize(career["Industry"])

    # Career exploration data currently provides the career
    # specialization/title information but not a separate
    # Related_Interest_Areas field.
    #
    # Therefore, interest-area overlap is calculated using
    # the student's career preference against the selected
    # career title.

    career_title = normalize(career["Job_Title"])

    interest_overlap = 0

    for interest in student_interests:
        if interest in career_title:
            interest_overlap = 1
            break

    industry_match = (
        1 if career_industry in preferred_industries else 0
    )

    interest_score = (
        interest_overlap * 0.50
        + industry_match * 0.50
    )

    return {
        "interest_overlap": interest_overlap,
        "industry_match": industry_match,
        "score": interest_score
    }


# ---------------------------------------------------------
# Overall Alignment
# ---------------------------------------------------------

def calculate_alignment_score(
    education_score,
    skill_score,
    interest_score
):
    return (
        education_score * 0.40
        + skill_score * 0.40
        + interest_score * 0.20
    )


# ---------------------------------------------------------
# Classification
# ---------------------------------------------------------

def classify_alignment(score):
    if score >= 0.70:
        return "High"

    if score >= 0.40:
        return "Medium"

    return "Low"


# ---------------------------------------------------------
# Main Alignment Analysis
# ---------------------------------------------------------

def analyze_alignment(student_id, occupation_id):
    student = get_student_profile(student_id)

    if student is None:
        return {
            "success": False,
            "message": "Student profile is unavailable."
        }

    career = retrieve_career_requirements(occupation_id)

    if career is None:
        return {
            "success": False,
            "message": "Career requirements are unavailable."
        }

    education = calculate_education_match(
        student,
        career
    )

    skills = calculate_skill_match(
        student,
        career
    )

    interests = calculate_interest_match(
        student,
        career
    )

    alignment_score = calculate_alignment_score(
        education["score"],
        skills["score"],
        interests["score"]
    )

    classification = classify_alignment(
        alignment_score
    )

    return {
        "success": True,
        "message": "Alignment analysis completed.",

        "student_id": student_id,

        "career": {
            "occupation_id": career["Occupation_Id"],
            "job_title": career["Job_Title"],
            "industry": career["Industry"]
        },

        "education_match": education,
        "skill_match": skills,
        "interest_match": interests,

        "alignment_score": alignment_score,
        "alignment_percentage": round(
            alignment_score * 100,
            2
        ),
        "classification": classification
    }