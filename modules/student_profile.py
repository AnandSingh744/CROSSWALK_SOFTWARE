from database import get_connection


# --------------------------------------------------
# Clean List
# --------------------------------------------------

def clean_list(items):
    """
    Remove empty and repeated entries.
    """

    cleaned = []

    for item in items:

        item = item.strip()

        if item and item not in cleaned:
            cleaned.append(item)

    return cleaned


# --------------------------------------------------
# Convert text to list
# --------------------------------------------------

def text_to_list(text):
    """
    Convert comma-separated text into a cleaned list.
    """

    if not text:
        return []

    items = text.split(",")

    return clean_list(items)


# --------------------------------------------------
# Convert list to database text
# --------------------------------------------------

def list_to_text(items):
    """
    Convert a list into the pipe-separated format
    used by the CROSSWALK datasets.
    """

    return "|".join(items)


# --------------------------------------------------
# Find Student
# --------------------------------------------------

def find_student_by_user(user_id):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                Student_Id,
                User_Id,
                Degree,
                Course,
                Specialization,
                College,
                Technical_Skills,
                Soft_Skills,
                Certifications,
                Areas_Of_Interest,
                Preferred_Industries,
                Career_Preferences,
                Profile_Status
            FROM students
            WHERE User_Id = ?
            """,
            (user_id,)
        )

        return cursor.fetchone()

    finally:
        conn.close()


# --------------------------------------------------
# Save Student Profile
# --------------------------------------------------

def save_student_profile(
    student_id,
    degree,
    course,
    specialization,
    college,
    technical_skills,
    soft_skills,
    certifications,
    areas_of_interest,
    preferred_industries,
    career_preferences
):

    # ----------------------------------------------
    # Required education validation
    # ----------------------------------------------

    required_fields = {
        "Degree": degree,
        "Course": course,
        "Specialization": specialization,
        "College": college
    }

    for field, value in required_fields.items():

        if not value or not value.strip():
            return {
                "success": False,
                "message": "Please complete all required fields to continue."
            }

    # ----------------------------------------------
    # Clean skills and interests
    # ----------------------------------------------

    technical_skills = clean_list(technical_skills)
    soft_skills = clean_list(soft_skills)
    certifications = clean_list(certifications)

    areas_of_interest = clean_list(areas_of_interest)
    preferred_industries = clean_list(preferred_industries)
    career_preferences = clean_list(career_preferences)

    # ----------------------------------------------
    # Determine profile status
    # ----------------------------------------------

    profile_status = "Complete"

    if not (
        technical_skills
        or soft_skills
        or certifications
    ):
        profile_status = "Incomplete"

    if not (
        areas_of_interest
        or preferred_industries
        or career_preferences
    ):
        profile_status = "Incomplete"

    # ----------------------------------------------
    # Store profile
    # ----------------------------------------------

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE students
            SET
                Degree = ?,
                Course = ?,
                Specialization = ?,
                College = ?,
                Technical_Skills = ?,
                Soft_Skills = ?,
                Certifications = ?,
                Areas_Of_Interest = ?,
                Preferred_Industries = ?,
                Career_Preferences = ?,
                Profile_Status = ?
            WHERE Student_Id = ?
            """,
            (
                degree.strip(),
                course.strip(),
                specialization.strip(),
                college.strip(),
                list_to_text(technical_skills),
                list_to_text(soft_skills),
                list_to_text(certifications),
                list_to_text(areas_of_interest),
                list_to_text(preferred_industries),
                list_to_text(career_preferences),
                profile_status,
                student_id
            )
        )

        conn.commit()

        return {
            "success": True,
            "message": "Profile saved",
            "profile_status": profile_status
        }

    except Exception as e:

        conn.rollback()

        return {
            "success": False,
            "message": f"Profile could not be saved: {e}"
        }

    finally:

        conn.close()