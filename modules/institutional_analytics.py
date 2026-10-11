from database import get_connection


def normalize(value):
    if value is None:
        return ""

    return str(value).strip().lower()


def find_courses(selection):
    """
    Find education records matching the selected
    course or specialization.
    """

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                Education_Id,
                Degree,
                Course,
                Specialization,
                College
            FROM education
        """)

        records = cursor.fetchall()

    finally:

        conn.close()


    courses = []

    selected = normalize(selection)

    for record in records:

        education_id = record[0]
        degree = record[1]
        course = record[2]
        specialization = record[3]
        college = record[4]

        if (
            normalize(course) == selected
            or normalize(specialization) == selected
        ):

            courses.append({
                "Education_Id": education_id,
                "Degree": degree,
                "Course": course,
                "Specialization": specialization,
                "College": college
            })

    return courses


def find_mapped_careers(course):
    """
    Find employment records whose degree matches
    the degree associated with the education record.
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
                Specialization,
                Employment_Status,
                Experience_Level
            FROM standardized_employment
            WHERE Job_Title IS NOT NULL
        """)

        records = cursor.fetchall()

    finally:

        conn.close()


    careers = []

    target_degree = normalize(
        course["Degree"]
    )


    for record in records:

        occupation_id = record[0]
        job_title = record[1]
        industry = record[2]
        degree = record[3]
        course_name = record[4]
        specialization = record[5]
        employment_status = record[6]
        experience_level = record[7]


        if normalize(degree) == target_degree:

            careers.append({
                "Occupation_Id": occupation_id,
                "Job_Title": job_title,
                "Industry": industry,
                "Degree": degree,
                "Course": course_name,
                "Specialization": specialization,
                "Employment_Status": employment_status,
                "Experience_Level": experience_level
            })


    return careers


def analyse_course_demand(courses):
    """
    Number of linked employment/career records
    for each degree represented by the selected field.
    """

    demand_stats = []

    for course in courses:

        careers = find_mapped_careers(course)

        demand_stats.append({
            "Degree": course["Degree"],
            "Course": course["Course"],
            "Specialization": course["Specialization"],
            "Career_Count": len(careers)
        })

    return demand_stats


def analyse_employment_outcomes(courses):
    """
    Analyse employment status and experience-level
    outcomes.

    Salary is not present in the current dataset,
    so salary information is marked unavailable.
    """

    outcome_stats = []


    for course in courses:

        careers = find_mapped_careers(course)


        if not careers:

            outcome_stats.append({
                "Degree": course["Degree"],
                "Course": course["Course"],
                "Employment_Status": {},
                "Experience_Level": {},
                "Salary": "Data unavailable"
            })

            continue


        employment_status = {}

        experience_levels = {}


        for career in careers:

            status = career["Employment_Status"]
            level = career["Experience_Level"]


            if status:

                employment_status[status] = (
                    employment_status.get(status, 0) + 1
                )


            if level:

                experience_levels[level] = (
                    experience_levels.get(level, 0) + 1
                )


        outcome_stats.append({
            "Degree": course["Degree"],
            "Course": course["Course"],
            "Employment_Status": employment_status,
            "Experience_Level": experience_levels,
            "Salary": "Data unavailable"
        })


    return outcome_stats


def identify_common_career_paths(courses):
    """
    Identify the most common job titles linked
    to the selected education field.
    """

    career_counts = {}


    for course in courses:

        careers = find_mapped_careers(course)


        for career in careers:

            job_title = career["Job_Title"]

            if job_title:

                career_counts[job_title] = (
                    career_counts.get(job_title, 0) + 1
                )


    sorted_careers = sorted(
        career_counts.items(),
        key=lambda item: item[1],
        reverse=True
    )


    return [
        {
            "Career": career,
            "Count": count
        }
        for career, count in sorted_careers
    ]


def identify_mismatch_patterns(courses):
    """
    Identify education records for which no
    matching employment career was found.
    """

    mismatch_patterns = []


    for course in courses:

        careers = find_mapped_careers(course)


        if not careers:

            mismatch_patterns.append({
                "Degree": course["Degree"],
                "Course": course["Course"],
                "Specialization": course["Specialization"],
                "Issue": "No mapped career found"
            })


    return mismatch_patterns


def get_available_fields():
    """
    Return unique courses and specializations
    available for institutional analysis.
    """

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT Course, Specialization
            FROM education
        """)

        records = cursor.fetchall()

    finally:

        conn.close()


    fields = set()


    for course, specialization in records:

        if course:
            fields.add(course)

        if specialization:
            fields.add(specialization)


    return sorted(fields)


def analyse_institutional_data(selection):
    """
    Main Module 8 process.
    """

    if not selection:

        return {
            "success": False,
            "message": "No course or field selected."
        }


    courses = find_courses(selection)


    if not courses:

        return {
            "success": False,
            "message": "Insufficient data is available for this request."
        }


    demand_stats = analyse_course_demand(
        courses
    )

    outcome_stats = analyse_employment_outcomes(
        courses
    )

    career_paths = identify_common_career_paths(
        courses
    )

    mismatch_patterns = identify_mismatch_patterns(
        courses
    )


    return {
        "success": True,
        "message": "Institutional analytics completed.",
        "selection": selection,
        "courses": courses,
        "demand_stats": demand_stats,
        "outcome_stats": outcome_stats,
        "career_paths": career_paths,
        "mismatch_patterns": mismatch_patterns
    }