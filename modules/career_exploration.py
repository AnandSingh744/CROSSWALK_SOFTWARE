from database import get_connection


# --------------------------------------------------
# Search or Browse Careers
# --------------------------------------------------

def search_or_browse_careers(search_term=None, browse_filter=None):
    """
    Search careers by keyword or browse careers by industry.
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                Occupation_Id,
                Job_Title,
                Industry,
                Degree,
                Course,
                Specialization
            FROM standardized_employment
            WHERE Job_Title IS NOT NULL
        """)

        records = cursor.fetchall()

    finally:
        conn.close()

    careers = []

    search_term = search_term.strip().lower() if search_term else ""
    browse_filter = browse_filter.strip().lower() if browse_filter else ""

    for record in records:

        occupation_id = record[0]
        job_title = record[1] or ""
        industry = record[2] or ""

        # No search/filter → return everything
        if not search_term and not browse_filter:
            careers.append(record)

        # Keyword search
        elif search_term:
            if (
                search_term in job_title.lower()
                or search_term in industry.lower()
            ):
                careers.append(record)

        # Industry browse
        elif browse_filter:
            if industry.lower() == browse_filter:
                careers.append(record)

    return careers


# --------------------------------------------------
# Retrieve Career Requirements
# --------------------------------------------------

def retrieve_career_requirements(occupation_id):
    """
    Retrieve details and required skills for a selected career.
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()

        # Find occupation
        cursor.execute("""
            SELECT
                Occupation_Id,
                Job_Title,
                Industry,
                Degree,
                Course,
                Specialization
            FROM standardized_employment
            WHERE Occupation_Id = ?
        """, (occupation_id,))

        occupation = cursor.fetchone()

        if occupation is None:
            return None

        job_title = occupation[1]

        # Find matching career in career catalog
        cursor.execute("""
            SELECT Career_Id
            FROM careers
            WHERE LOWER(Career_Name) = LOWER(?)
            LIMIT 1
        """, (job_title,))

        career = cursor.fetchone()

        required_skills = []

        if career is not None:

            career_id = career[0]

            cursor.execute("""
                SELECT
                    s.Skill_Name
                FROM career_skills cs
                JOIN skills s
                    ON cs.Skill_Id = s.Skill_Id
                WHERE cs.Career_Id = ?
                  AND cs.Requirement_Type = 'Required'
            """, (career_id,))

            skill_rows = cursor.fetchall()

            for row in skill_rows:
                required_skills.append(row[0])

    finally:
        conn.close()

    return {
        "Occupation_Id": occupation[0],
        "Job_Title": occupation[1],
        "Industry": occupation[2],
        "Degree_Mapping": occupation[3],
        "Course": occupation[4],
        "Specialization": occupation[5],
        "Required_Skills": required_skills
    }


# --------------------------------------------------
# Select Desired Career
# --------------------------------------------------

def select_desired_career(careers, occupation_id):
    """
    Validate and return the selected career ID.
    """

    if not occupation_id:
        return None

    for career in careers:

        if career[0] == occupation_id:
            return career[0]

    return None


# --------------------------------------------------
# Main Career Exploration Process
# --------------------------------------------------

def explore_careers(
    search_term=None,
    browse_filter=None,
    selected_career_id=None
):
    """
    Complete Module 4 career exploration process.
    """

    careers = search_or_browse_careers(
        search_term=search_term,
        browse_filter=browse_filter
    )

    # No matching careers
    if not careers:
        return {
            "success": False,
            "message": "Insufficient data is available for this request.",
            "careers": [],
            "selected_career": None
        }

    # No career selected yet
    if selected_career_id is None:
        return {
            "success": True,
            "message": "Careers found.",
            "careers": careers,
            "selected_career": None
        }

    selected_id = select_desired_career(
        careers,
        selected_career_id
    )

    if selected_id is None:
        return {
            "success": False,
            "message": "No career selected.",
            "careers": careers,
            "selected_career": None
        }

    details = retrieve_career_requirements(selected_id)

    if details is None:
        return {
            "success": False,
            "message": "Career requirements are unavailable.",
            "careers": careers,
            "selected_career": None
        }

    return {
        "success": True,
        "message": "Career selected successfully.",
        "careers": careers,
        "selected_career": details
    }