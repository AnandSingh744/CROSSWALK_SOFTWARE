from database import get_connection
from modules.career_exploration import retrieve_career_requirements


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
# Retrieve Student Skills
# ---------------------------------------------------------

def retrieve_student_skills(student_id):
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                Technical_Skills,
                Soft_Skills,
                Certifications
            FROM students
            WHERE Student_Id = ?
        """, (student_id,))

        profile = cursor.fetchone()

        if profile is None:
            return []

        technical_skills = split_values(profile[0])
        soft_skills = split_values(profile[1])
        certifications = split_values(profile[2])

        return technical_skills + soft_skills + certifications

    finally:
        conn.close()


# ---------------------------------------------------------
# Identify Missing Skills
# ---------------------------------------------------------

def identify_missing_skills(student_skills, required_skills):
    student_skill_names = {
        normalize(skill)
        for skill in student_skills
    }

    missing = []

    for skill in required_skills:
        if normalize(skill) not in student_skill_names:
            missing.append(skill)

    return missing


# ---------------------------------------------------------
# Categorize Gaps
# ---------------------------------------------------------

def categorize_gaps(missing_skills):
    if not missing_skills:
        return {
            "Technical_Gaps": [],
            "Soft_Gaps": []
        }

    conn = get_connection()

    try:
        cursor = conn.cursor()

        technical_gaps = []
        soft_gaps = []

        for skill in missing_skills:

            cursor.execute("""
                SELECT Category
                FROM skills
                WHERE LOWER(Skill_Name) = LOWER(?)
                LIMIT 1
            """, (skill,))

            row = cursor.fetchone()

            if row is not None and normalize(row[0]) == "technical":
                technical_gaps.append(skill)
            else:
                soft_gaps.append(skill)

        return {
            "Technical_Gaps": technical_gaps,
            "Soft_Gaps": soft_gaps
        }

    finally:
        conn.close()


# ---------------------------------------------------------
# Recommend Courses
# ---------------------------------------------------------

def recommend_courses(missing_skills):
    if not missing_skills:
        return []

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                Course_Id,
                Course_Name,
                Skills_Covered,
                Level,
                Duration_Weeks
            FROM courses
        """)

        courses = cursor.fetchall()

    finally:
        conn.close()

    recommendations = []

    missing_normalized = {
        normalize(skill)
        for skill in missing_skills
    }

    for course in courses:

        course_id = course[0]
        course_name = course[1]
        skills_covered = split_values(course[2])
        level = course[3]
        duration = course[4]

        covered = []

        for skill in missing_skills:
            for course_skill in skills_covered:

                if normalize(skill) == normalize(course_skill):
                    covered.append(skill)
                    break

        if covered:
            recommendations.append({
                "Course_Id": course_id,
                "Course_Name": course_name,
                "Covered_Skills": covered,
                "Relevance": len(covered),
                "Level": level,
                "Duration_Weeks": duration
            })

    # Highest number of covered missing skills first
    recommendations.sort(
        key=lambda item: item["Relevance"],
        reverse=True
    )

    return recommendations


# ---------------------------------------------------------
# Find Uncovered Skills
# ---------------------------------------------------------

def find_uncovered_skills(
    missing_skills,
    recommendations
):
    covered_by_courses = set()

    for recommendation in recommendations:
        for skill in recommendation["Covered_Skills"]:
            covered_by_courses.add(normalize(skill))

    uncovered = []

    for skill in missing_skills:
        if normalize(skill) not in covered_by_courses:
            uncovered.append(skill)

    return uncovered


# ---------------------------------------------------------
# Main Module 6 Process
# ---------------------------------------------------------

def analyze_skill_gap(student_id, occupation_id):

    # 1. Retrieve student skills
    student_skills = retrieve_student_skills(student_id)

    if not student_skills:
        return {
            "success": False,
            "message": "Student skills are unavailable.",
            "gaps": None,
            "recommendations": [],
            "uncovered_skills": []
        }

    # 2. Retrieve career requirements
    career = retrieve_career_requirements(occupation_id)

    if career is None:
        return {
            "success": False,
            "message": "Career requirements are unavailable.",
            "gaps": None,
            "recommendations": [],
            "uncovered_skills": []
        }

    required_skills = career["Required_Skills"]

    if not required_skills:
        return {
            "success": False,
            "message": "Required career skills are unavailable.",
            "gaps": None,
            "recommendations": [],
            "uncovered_skills": []
        }

    # 3. Find missing skills
    missing_skills = identify_missing_skills(
        student_skills,
        required_skills
    )

    # No gap
    if not missing_skills:
        return {
            "success": True,
            "message": "No skill gaps found.",
            "career": career,
            "student_skills": student_skills,
            "required_skills": required_skills,
            "missing_skills": [],
            "gaps": {
                "Technical_Gaps": [],
                "Soft_Gaps": []
            },
            "recommendations": [],
            "uncovered_skills": []
        }

    # 4. Categorize gaps
    gaps = categorize_gaps(missing_skills)

    # 5. Recommend courses
    recommendations = recommend_courses(
        missing_skills
    )

    # 6. Find uncovered skills
    uncovered_skills = find_uncovered_skills(
        missing_skills,
        recommendations
    )

    return {
        "success": True,
        "message": "Skill gap analysis completed.",
        "career": career,
        "student_skills": student_skills,
        "required_skills": required_skills,
        "missing_skills": missing_skills,
        "gaps": gaps,
        "recommendations": recommendations,
        "uncovered_skills": uncovered_skills
    }