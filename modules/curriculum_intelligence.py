from database import get_connection


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


# =========================================================
# FIND CAREERS
# =========================================================

def find_careers(selection_type, selection):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                Occupation_Id,
                Job_Title,
                Industry
            FROM standardized_employment
            WHERE Job_Title IS NOT NULL
        """)

        records = cursor.fetchall()

    finally:

        conn.close()


    careers = []

    selected = normalize(selection)


    for record in records:

        occupation_id = record[0]
        job_title = record[1]
        industry = record[2]


        if selection_type == "Industry":

            if normalize(industry) == selected:

                careers.append({
                    "Occupation_Id": occupation_id,
                    "Job_Title": job_title,
                    "Industry": industry
                })


        elif selection_type == "Career":

            if normalize(job_title) == selected:

                careers.append({
                    "Occupation_Id": occupation_id,
                    "Job_Title": job_title,
                    "Industry": industry
                })


    return careers


# =========================================================
# FIND CAREER IDS
# =========================================================

def find_career_ids(careers):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        career_ids = []


        for career in careers:

            cursor.execute("""
                SELECT Career_Id
                FROM careers
                WHERE LOWER(Career_Name) = LOWER(?)
            """, (career["Job_Title"],))

            rows = cursor.fetchall()


            for row in rows:

                if row[0] not in career_ids:

                    career_ids.append(row[0])


    finally:

        conn.close()


    return career_ids


# =========================================================
# RETRIEVE RISING SKILLS
# =========================================================

def retrieve_skill_demand_trends(careers):

    career_ids = find_career_ids(careers)


    if not career_ids:

        return []


    conn = get_connection()

    try:

        cursor = conn.cursor()


        placeholders = ",".join(
            "?"
            for _ in career_ids
        )


        query = f"""
            SELECT DISTINCT
                s.Skill_Id,
                s.Skill_Name,
                s.Category,
                s.Domain,
                s.Demand_Trend
            FROM career_skills cs
            JOIN skills s
                ON cs.Skill_Id = s.Skill_Id
            WHERE cs.Career_Id IN ({placeholders})
              AND LOWER(s.Demand_Trend) = 'rising'
        """


        cursor.execute(
            query,
            career_ids
        )


        rows = cursor.fetchall()


    finally:

        conn.close()


    trending = []


    for row in rows:

        trending.append({
            "Skill_Id": row[0],
            "Skill_Name": row[1],
            "Category": row[2],
            "Domain": row[3],
            "Demand_Trend": row[4]
        })


    return trending


# =========================================================
# RETRIEVE CURRICULUM
# =========================================================

def retrieve_curriculum():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                Subject_Id,
                Subject_Name,
                Degree,
                Course,
                Semester,
                Credits,
                Subject_Type,
                Skills_Taught
            FROM curriculum
        """)

        rows = cursor.fetchall()

    finally:

        conn.close()


    curriculum = []


    for row in rows:

        curriculum.append({
            "Subject_Id": row[0],
            "Subject_Name": row[1],
            "Degree": row[2],
            "Course": row[3],
            "Semester": row[4],
            "Credits": row[5],
            "Subject_Type": row[6],
            "Skills_Taught": split_values(row[7])
        })


    return curriculum


# =========================================================
# COMPARE WITH CURRICULUM
# =========================================================

def compare_with_curriculum(trending):

    curriculum = retrieve_curriculum()


    if not curriculum:

        return None


    taught_skills = set()


    for subject in curriculum:

        for skill in subject["Skills_Taught"]:

            taught_skills.add(
                normalize(skill)
            )


    gaps = []


    for skill in trending:

        if normalize(
            skill["Skill_Name"]
        ) not in taught_skills:

            gaps.append(skill)


    return gaps


# =========================================================
# MAP GAPS TO SUBJECTS
# =========================================================

def map_gaps_to_subjects(gaps):

    curriculum = retrieve_curriculum()

    recommendations = []


    for gap in gaps:

        gap_name = normalize(
            gap["Skill_Name"]
        )


        matching_subjects = []


        for subject in curriculum:

            for taught_skill in subject[
                "Skills_Taught"
            ]:

                if normalize(
                    taught_skill
                ) == gap_name:

                    matching_subjects.append(
                        subject
                    )

                    break


        recommendations.append({
            "Skill": gap["Skill_Name"],
            "Subjects": matching_subjects
        })


    return recommendations


# =========================================================
# MAIN CURRICULUM ANALYSIS
# =========================================================

def analyse_curriculum(
    selection_type,
    selection
):

    if not selection:

        return {
            "success": False,
            "message": "No industry or career selected."
        }


    careers = find_careers(
        selection_type,
        selection
    )


    if not careers:

        return {
            "success": False,
            "message": (
                "Insufficient data is available "
                "for this request."
            )
        }


    curriculum = retrieve_curriculum()


    if not curriculum:

        return {
            "success": False,
            "message": "Curriculum data unavailable."
        }


    trending = retrieve_skill_demand_trends(
        careers
    )


    if not trending:

        return {
            "success": False,
            "message": (
                "Skill demand trend data unavailable."
            )
        }


    gaps = compare_with_curriculum(
        trending
    )


    if gaps is None:

        return {
            "success": False,
            "message": "Curriculum data unavailable."
        }


    if not gaps:

        return {
            "success": True,
            "message": (
                "Curriculum already covers "
                "the trending skills."
            ),
            "selection": selection,
            "selection_type": selection_type,
            "careers": careers,
            "trending_skills": trending,
            "gaps": [],
            "recommendations": []
        }


    recommendations = map_gaps_to_subjects(
        gaps
    )


    return {
        "success": True,
        "message": (
            "Curriculum intelligence analysis "
            "completed."
        ),
        "selection": selection,
        "selection_type": selection_type,
        "careers": careers,
        "trending_skills": trending,
        "gaps": gaps,
        "recommendations": recommendations
    }


# =========================================================
# AVAILABLE SELECTIONS
# =========================================================

def get_curriculum_selections():

    conn = get_connection()

    try:

        cursor = conn.cursor()


        cursor.execute("""
            SELECT DISTINCT Industry
            FROM standardized_employment
            WHERE Industry IS NOT NULL
              AND TRIM(Industry) != ''
        """)

        industries = [
            row[0]
            for row in cursor.fetchall()
        ]


        cursor.execute("""
            SELECT DISTINCT Job_Title
            FROM standardized_employment
            WHERE Job_Title IS NOT NULL
              AND TRIM(Job_Title) != ''
        """)

        careers = [
            row[0]
            for row in cursor.fetchall()
        ]


    finally:

        conn.close()


    return (
        sorted(industries),
        sorted(careers)
    )