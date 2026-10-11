import streamlit as st
from modules.institutional_analytics import (
    get_available_fields,
    analyse_institutional_data
)

from modules.reporting import (
    get_report_options,
    get_report_selections,
    build_report
)

from modules.curriculum_intelligence import (
    get_curriculum_selections,
    analyse_curriculum
)

from modules.authentication import login_user
from modules.student_profile import (
    find_student_by_user,
    save_student_profile,
    text_to_list
)
from modules.career_exploration import (
    search_or_browse_careers,
    retrieve_career_requirements
)
from modules.alignment_analysis import analyze_alignment
from modules.skill_gap_recommendation import analyze_skill_gap


st.set_page_config(
    page_title="CROSSWALK",
    page_icon="🎓",
    layout="wide"
)


# =========================================================
# SESSION STATE
# =========================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "session" not in st.session_state:
    st.session_state.session = None

if "selected_career_id" not in st.session_state:
    st.session_state.selected_career_id = None

if "career_analysis" not in st.session_state:
    st.session_state.career_analysis = None

if "institutional_analysis" not in st.session_state:
    st.session_state.institutional_analysis = None

if "curriculum_analysis" not in st.session_state:
    st.session_state.curriculum_analysis = None

if "report_result" not in st.session_state:
    st.session_state.report_result = None

# =========================================================
# LOGIN
# =========================================================

def show_login():

    st.title("🎓 CROSSWALK")
    st.caption(
        "Career Guidance and Curriculum Intelligence System"
    )

    st.divider()

    st.subheader("Login")

    email = st.text_input("Email")
    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button(
        "Login",
        type="primary",
        use_container_width=True
    ):

        if not email or not password:
            st.error(
                "Please enter both email and password."
            )

        else:

            result = login_user(
                email,
                password
            )

            if result["success"]:

                st.session_state.logged_in = True
                st.session_state.session = result["session"]

                st.rerun()

            else:
                st.error(result["message"])


# =========================================================
# STUDENT PROFILE
# =========================================================

def show_student_profile():

    session = st.session_state.session

    student = find_student_by_user(
        session["user_id"]
    )

    if student is None:

        st.error(
            "Student profile could not be found."
        )

        return

    (
        student_id,
        user_id,
        existing_degree,
        existing_course,
        existing_specialization,
        existing_college,
        existing_technical_skills,
        existing_soft_skills,
        existing_certifications,
        existing_interests,
        existing_industries,
        existing_preferences,
        existing_status
    ) = student


    st.subheader("Student Profile")

    st.write(
        "Update your education, skills and career interests."
    )


    # -----------------------------------------------------
    # Education
    # -----------------------------------------------------

    st.markdown("### Education")

    degree = st.text_input(
        "Degree",
        value=existing_degree or ""
    )

    course = st.text_input(
        "Course",
        value=existing_course or ""
    )

    specialization = st.text_input(
        "Specialization",
        value=existing_specialization or ""
    )

    college = st.text_input(
        "College",
        value=existing_college or ""
    )


    # -----------------------------------------------------
    # Skills
    # -----------------------------------------------------

    st.markdown("### Skills")

    technical_skills = st.text_area(
        "Technical Skills",
        value=(
            existing_technical_skills.replace(
                "|",
                ", "
            )
            if existing_technical_skills
            else ""
        ),
        help="Example: Python, SQL, Pandas"
    )

    soft_skills = st.text_area(
        "Soft Skills",
        value=(
            existing_soft_skills.replace(
                "|",
                ", "
            )
            if existing_soft_skills
            else ""
        ),
        help="Example: Communication, Leadership"
    )

    certifications = st.text_area(
        "Certifications",
        value=(
            existing_certifications.replace(
                "|",
                ", "
            )
            if existing_certifications
            else ""
        )
    )


    # -----------------------------------------------------
    # Interests
    # -----------------------------------------------------

    st.markdown("### Career Interests")

    areas_of_interest = st.text_area(
        "Areas of Interest",
        value=(
            existing_interests.replace(
                "|",
                ", "
            )
            if existing_interests
            else ""
        ),
        help="Example: Artificial Intelligence, Data Science"
    )

    preferred_industries = st.text_area(
        "Preferred Industries",
        value=(
            existing_industries.replace(
                "|",
                ", "
            )
            if existing_industries
            else ""
        ),
        help="Example: Technology, Finance"
    )

    career_preferences = st.text_area(
        "Career Preferences",
        value=(
            existing_preferences.replace(
                "|",
                ", "
            )
            if existing_preferences
            else ""
        ),
        help="Example: Data Scientist, ML Engineer"
    )


    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

    if st.button(
        "Save Profile",
        type="primary"
    ):

        result = save_student_profile(

            student_id=student_id,

            degree=degree,

            course=course,

            specialization=specialization,

            college=college,

            technical_skills=text_to_list(
                technical_skills
            ),

            soft_skills=text_to_list(
                soft_skills
            ),

            certifications=text_to_list(
                certifications
            ),

            areas_of_interest=text_to_list(
                areas_of_interest
            ),

            preferred_industries=text_to_list(
                preferred_industries
            ),

            career_preferences=text_to_list(
                career_preferences
            )
        )


        if result["success"]:

            st.success(
                result["message"]
            )

            if result["profile_status"] == "Complete":

                st.success(
                    "Profile Status: Complete"
                )

            else:

                st.warning(
                    "Profile Status: Incomplete. "
                    "Please add your skills and interests."
                )

        else:

            st.error(
                result["message"]
            )


# =========================================================
# CAREER EXPLORATION
# =========================================================

def show_career_exploration():

    st.subheader("Career Exploration")

    st.write(
        "Search for careers or browse them by industry."
    )


    col1, col2 = st.columns([2, 1])


    with col1:

        search_term = st.text_input(
            "Search career",
            placeholder="Example: Data, Engineer, Analyst"
        )


    with col2:

        industries = [
            "All Industries",
            "Technology",
            "Finance & Banking",
            "Healthcare",
            "Consulting",
            "Education",
            "Manufacturing",
            "Marketing"
        ]

        selected_industry = st.selectbox(
            "Industry",
            industries
        )


    browse_filter = None

    if selected_industry != "All Industries":
        browse_filter = selected_industry


    careers = search_or_browse_careers(
        search_term=search_term,
        browse_filter=browse_filter
    )


    if not careers:

        st.info(
            "No matching careers were found."
        )

        return


    st.write(
        f"**{len(careers)} careers found**"
    )


    # -----------------------------------------------------
    # Career table
    # -----------------------------------------------------

    for career in careers:

        occupation_id = career[0]
        job_title = career[1]
        industry = career[2]
        degree = career[3]
        course = career[4]
        specialization = career[5]


        with st.container(border=True):

            col1, col2, col3 = st.columns(
                [2, 2, 1]
            )


            with col1:

                st.markdown(
                    f"**{job_title}**"
                )

                st.caption(
                    occupation_id
                )


            with col2:

                st.write(
                    f"Industry: {industry}"
                )

                st.caption(
                    f"{degree or 'Any degree'}"
                )


            with col3:

                if st.button(
                    "Select",
                    key=f"select_{occupation_id}"
                ):

                    st.session_state.selected_career_id = (
                        occupation_id
                    )

                    st.session_state.career_analysis = None

                    st.rerun()


    # -----------------------------------------------------
    # Selected career
    # -----------------------------------------------------

    selected_id = st.session_state.selected_career_id

    if selected_id:

        st.divider()

        career = retrieve_career_requirements(
            selected_id
        )


        if career:

            st.subheader(
                f"{career['Job_Title']} — {career['Industry']}"
            )


            col1, col2 = st.columns(2)


            with col1:

                st.markdown("### Career Requirements")

                st.write(
                    f"**Degree:** "
                    f"{career['Degree_Mapping'] or 'Not specified'}"
                )

                st.write(
                    f"**Course:** "
                    f"{career['Course'] or 'Not specified'}"
                )

                st.write(
                    f"**Specialization:** "
                    f"{career['Specialization'] or 'Not specified'}"
                )


            with col2:

                st.markdown("### Required Skills")

                if career["Required_Skills"]:

                    for skill in career["Required_Skills"]:
                        st.write(f"• {skill}")

                else:

                    st.write(
                        "No required skills available."
                    )


            if st.button(
                "Analyze My Alignment",
                type="primary"
            ):

                student = find_student_by_user(
                    st.session_state.session["user_id"]
                )

                if student is None:

                    st.error(
                        "Student profile could not be found."
                    )

                else:

                    student_id = student[0]

                    analysis = analyze_alignment(
                        student_id,
                        selected_id
                    )

                    skill_gap = analyze_skill_gap(
                        student_id,
                        selected_id
                    )

                    st.session_state.career_analysis = {
                        "alignment": analysis,
                        "skill_gap": skill_gap
                    }

                    st.rerun()


# =========================================================
# CAREER ANALYSIS
# =========================================================

def show_career_analysis():

    analysis_data = st.session_state.career_analysis

    if not analysis_data:
        return


    alignment = analysis_data["alignment"]

    skill_gap = analysis_data["skill_gap"]


    st.divider()

    st.header("Career Analysis")


    if not alignment["success"]:

        st.error(
            alignment["message"]
        )

        return


    # -----------------------------------------------------
    # Career heading
    # -----------------------------------------------------

    career = alignment["career"]

    st.subheader(
        f"{career['job_title']} — {career['industry']}"
    )


    # -----------------------------------------------------
    # Alignment summary
    # -----------------------------------------------------

    score = alignment["alignment_percentage"]

    classification = alignment["classification"]


    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "Alignment Score",
            f"{score}%"
        )


    with col2:

        st.metric(
            "Classification",
            classification
        )


    with col3:

        matched = len(
            alignment["skill_match"]["matched_skills"]
        )

        required = len(
            alignment["skill_match"]["matched_skills"]
        ) + len(
            alignment["skill_match"]["missing_skills"]
        )

        st.metric(
            "Skills Matched",
            f"{matched}/{required}"
        )


    st.progress(
        min(max(score / 100, 0), 1)
    )


    # -----------------------------------------------------
    # Match breakdown
    # -----------------------------------------------------

    st.markdown("### Match Breakdown")


    education = alignment["education_match"]
    skills = alignment["skill_match"]
    interests = alignment["interest_match"]


    col1, col2, col3 = st.columns(3)


    with col1:

        st.write("**Education**")

        st.progress(
            education["score"]
        )

        st.caption(
            f"{education['score'] * 100:.0f}%"
        )


    with col2:

        st.write("**Skills**")

        st.progress(
            skills["score"]
        )

        st.caption(
            f"{skills['score'] * 100:.0f}%"
        )


    with col3:

        st.write("**Interests**")

        st.progress(
            interests["score"]
        )

        st.caption(
            f"{interests['score'] * 100:.0f}%"
        )


    # -----------------------------------------------------
    # Skills
    # -----------------------------------------------------

    st.markdown("### Skill Analysis")


    col1, col2 = st.columns(2)


    with col1:

        st.write("**Matched Skills**")

        if skills["matched_skills"]:

            for skill in skills["matched_skills"]:
                st.write(f"✓ {skill}")

        else:

            st.info(
                "No required skills matched."
            )


    with col2:

        st.write("**Missing Skills**")

        if skills["missing_skills"]:

            for skill in skills["missing_skills"]:
                st.write(f"• {skill}")

        else:

            st.success(
                "No missing required skills."
            )


    # -----------------------------------------------------
    # Skill gap
    # -----------------------------------------------------

    if skill_gap["success"]:

        st.markdown("### Skill Gap")


        technical_gaps = skill_gap["gaps"][
            "Technical_Gaps"
        ]

        soft_gaps = skill_gap["gaps"][
            "Soft_Gaps"
        ]


        col1, col2 = st.columns(2)


        with col1:

            st.write("**Technical Gaps**")

            if technical_gaps:

                for skill in technical_gaps:
                    st.write(f"• {skill}")

            else:

                st.write("None")


        with col2:

            st.write("**Soft Skill Gaps**")

            if soft_gaps:

                for skill in soft_gaps:
                    st.write(f"• {skill}")

            else:

                st.write("None")


        # -------------------------------------------------
        # Recommendations
        # -------------------------------------------------

        recommendations = skill_gap[
            "recommendations"
        ]


        st.markdown(
            "### Recommended Courses"
        )


        if recommendations:

            for course in recommendations:

                with st.expander(
                    f"{course['Course_Name']} "
                    f"— covers {course['Relevance']} gap(s)"
                ):

                    col1, col2, col3 = st.columns(3)


                    with col1:

                        st.write(
                            f"**Level:** "
                            f"{course['Level']}"
                        )


                    with col2:

                        st.write(
                            f"**Duration:** "
                            f"{course['Duration_Weeks']} weeks"
                        )


                    with col3:

                        st.write(
                            "**Skills covered:** "
                            + ", ".join(
                                course["Covered_Skills"]
                            )
                        )


        else:

            st.info(
                "No course recommendations available."
            )


        uncovered = skill_gap[
            "uncovered_skills"
        ]


        if uncovered:

            st.warning(
                "No available course was found for: "
                + ", ".join(uncovered)
            )


# =========================================================
# STUDENT DASHBOARD
# =========================================================

def show_student_dashboard():

    session = st.session_state.session


    st.sidebar.title("CROSSWALK")

    st.sidebar.caption(
        f"Welcome, {session['name']}"
    )


    page = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "Student Profile",
            "Career Exploration"
        ]
    )


    if st.sidebar.button("Logout"):

        st.session_state.logged_in = False
        st.session_state.session = None
        st.session_state.selected_career_id = None
        st.session_state.career_analysis = None

        st.rerun()


    if page == "Dashboard":

        st.title("Student Dashboard")

        st.write(
            "Explore careers and understand how well "
            "your current profile matches them."
        )

        st.divider()

        show_career_analysis()


        if not st.session_state.career_analysis:

            st.info(
                "Go to **Career Exploration** to select "
                "a career and analyze your alignment."
            )


    elif page == "Student Profile":

        st.title("Student Profile")

        show_student_profile()


    elif page == "Career Exploration":

        st.title("Career Exploration")

        show_career_exploration()

        show_career_analysis()


# =========================================================
# OTHER ROLE DASHBOARDS
# =========================================================

def show_institutional_dashboard():
    page = st.sidebar.radio(
    "Navigation",
    [
        "Institutional Analytics",
        "Reports"
    ]
)

    if page == "Reports":
        show_reporting()
        return

    session = st.session_state.session

    st.sidebar.title("CROSSWALK")

    st.sidebar.caption(
        f"Welcome, {session['name']}"
    )

    if st.sidebar.button("Logout"):

        logout()


    st.title("Institutional Analytics")

    st.write(
        "Analyse course demand, employment outcomes "
        "and education-career trends."
    )

    st.divider()


    # =====================================================
    # FIELD SELECTION
    # =====================================================

    st.subheader("Select Course or Field")

    fields = get_available_fields()


    if not fields:

        st.warning(
            "Data unavailable: no education fields "
            "are available for analysis."
        )

        return


    selected_field = st.selectbox(
        "Course / Specialization",
        fields
    )


    if st.button(
        "Analyse",
        type="primary"
    ):

        result = analyse_institutional_data(
            selected_field
        )

        st.session_state.institutional_analysis = result


    # =====================================================
    # RESULTS
    # =====================================================

    if "institutional_analysis" not in st.session_state:

        st.info(
            "Select a course or field and click "
            "**Analyse** to view institutional insights."
        )

        return


    result = st.session_state.institutional_analysis


    if not result["success"]:

        st.warning(
            result["message"]
        )

        return


    st.divider()

    st.header(
        f"Analysis: {result['selection']}"
    )


    # =====================================================
    # SUMMARY METRICS
    # =====================================================

    total_records = len(
        result["courses"]
    )

    total_careers = sum(
        item["Career_Count"]
        for item in result["demand_stats"]
    )

    unique_careers = len(
        result["career_paths"]
    )

    mismatches = len(
        result["mismatch_patterns"]
    )


    col1, col2, col3, col4 = st.columns(4)


    with col1:

        st.metric(
            "Education Records",
            total_records
        )


    with col2:

        st.metric(
            "Career Records",
            total_careers
        )


    with col3:

        st.metric(
            "Career Paths",
            unique_careers
        )


    with col4:

        st.metric(
            "Mismatch Records",
            mismatches
        )


    # =====================================================
    # COURSE DEMAND
    # =====================================================

    st.subheader("Course / Field Demand")

    demand_stats = result[
        "demand_stats"
    ]


    if demand_stats:

        demand_data = {

            item["Degree"]:
            item["Career_Count"]

            for item in demand_stats
        }


        st.bar_chart(
            demand_data
        )

    else:

        st.info(
            "Data unavailable."
        )


    # =====================================================
    # EMPLOYMENT OUTCOMES
    # =====================================================

    st.subheader("Employment Outcomes")


    outcome_stats = result[
        "outcome_stats"
    ]


    for outcome in outcome_stats:

        st.markdown(
            f"**{outcome['Degree']} — "
            f"{outcome['Course']}**"
        )


        statuses = outcome[
            "Employment_Status"
        ]


        if statuses:

            status_columns = st.columns(
                len(statuses)
            )


            for column, (status, count) in zip(
                status_columns,
                statuses.items()
            ):

                with column:

                    st.metric(
                        status,
                        count
                    )

        else:

            st.info(
                "Employment outcome data unavailable."
            )


        experience = outcome[
            "Experience_Level"
        ]


        if experience:

            st.write(
                "**Experience Level Distribution**"
            )

            st.bar_chart(
                experience
            )


        st.caption(
            "Salary information: "
            + outcome["Salary"]
        )


    # =====================================================
    # COMMON CAREER PATHS
    # =====================================================

    st.subheader("Common Career Paths")


    career_paths = result[
        "career_paths"
    ]


    if career_paths:

        career_chart = {

            item["Career"]:
            item["Count"]

            for item in career_paths[:10]
        }


        st.bar_chart(
            career_chart
        )


        st.write(
            "Top career paths:"
        )


        for item in career_paths[:10]:

            st.write(
                f"• **{item['Career']}** — "
                f"{item['Count']} record(s)"
            )

    else:

        st.info(
            "Career path data unavailable."
        )


    # =====================================================
    # MISMATCH PATTERNS
    # =====================================================

    st.subheader(
        "Education–Career Mismatch Patterns"
    )


    mismatch_patterns = result[
        "mismatch_patterns"
    ]


    if mismatch_patterns:

        st.warning(
            f"{len(mismatch_patterns)} "
            "education record(s) have no mapped "
            "career."
        )


        for mismatch in mismatch_patterns:

            st.write(
                f"• **{mismatch['Degree']}** — "
                f"{mismatch['Course']} — "
                f"{mismatch['Specialization']}"
            )

            st.caption(
                mismatch["Issue"]
            )

    else:

        st.success(
            "No education-career mismatches "
            "were found."
        )


def show_curriculum_dashboard():
    page = st.sidebar.radio(
    "Navigation",
    [
        "Curriculum Intelligence",
        "Reports"
    ]
)

    if page == "Reports":
        show_reporting()
        return
    session = st.session_state.session

    st.sidebar.title("CROSSWALK")

    st.sidebar.caption(
        f"Welcome, {session['name']}"
    )

    if st.sidebar.button("Logout"):

        logout()


    st.title("Curriculum Intelligence")

    st.write(
        "Identify rising industry skills and compare "
        "them with the existing curriculum."
    )

    st.divider()


    # =====================================================
    # SELECTION
    # =====================================================

    st.subheader("Select Analysis")

    industries, careers = (
        get_curriculum_selections()
    )


    selection_type = st.radio(
        "Analyse by",
        ["Industry", "Career"],
        horizontal=True
    )


    if selection_type == "Industry":

        if not industries:

            st.warning(
                "Industry data unavailable."
            )

            return


        selection = st.selectbox(
            "Industry",
            industries
        )


    else:

        if not careers:

            st.warning(
                "Career data unavailable."
            )

            return


        selection = st.selectbox(
            "Career",
            careers
        )


    if st.button(
        "Analyse Curriculum",
        type="primary"
    ):

        result = analyse_curriculum(
            selection_type,
            selection
        )

        st.session_state.curriculum_analysis = (
            result
        )


    # =====================================================
    # RESULTS
    # =====================================================

    if (
        "curriculum_analysis"
        not in st.session_state
        or st.session_state.curriculum_analysis
        is None
    ):

        st.info(
            "Select an industry or career and click "
            "**Analyse Curriculum**."
        )

        return


    result = st.session_state.curriculum_analysis


    if not result["success"]:

        st.warning(
            result["message"]
        )

        return


    st.divider()


    st.header(
        f"Analysis: {result['selection']}"
    )


    # =====================================================
    # SUMMARY
    # =====================================================

    trending = result[
        "trending_skills"
    ]

    gaps = result[
        "gaps"
    ]

    careers_found = result[
        "careers"
    ]


    col1, col2, col3 = st.columns(3)


    with col1:

        st.metric(
            "Related Careers",
            len(careers_found)
        )


    with col2:

        st.metric(
            "Rising Skills",
            len(trending)
        )


    with col3:

        st.metric(
            "Curriculum Gaps",
            len(gaps)
        )


    # =====================================================
    # RELATED CAREERS
    # =====================================================

    st.subheader("Related Careers")


    career_names = sorted(
        set(
            career["Job_Title"]
            for career in careers_found
        )
    )


    for career_name in career_names:

        st.write(
            f"• {career_name}"
        )


    # =====================================================
    # TRENDING SKILLS
    # =====================================================

    st.subheader(
        "Trending Industry Skills"
    )


    for skill in trending:

        st.write(
            f"• **{skill['Skill_Name']}** "
            f"— {skill['Category']}"
        )


    # =====================================================
    # CURRICULUM GAPS
    # =====================================================

    st.subheader(
        "Trending Skills Missing from Curriculum"
    )


    if not gaps:

        st.success(
            "Curriculum already covers the "
            "trending skills."
        )

        return


    for gap in gaps:

        st.warning(
            gap["Skill_Name"]
        )


    # =====================================================
    # RECOMMENDATIONS
    # =====================================================

    st.subheader(
        "Recommended Subjects"
    )


    recommendations = result[
        "recommendations"
    ]


    for recommendation in recommendations:

        skill = recommendation["Skill"]

        subjects = recommendation[
            "Subjects"
        ]


        with st.expander(
            f"{skill}"
        ):

            if subjects:

                for subject in subjects:

                    st.write(
                        f"• **{subject['Subject_Name']}**"
                    )

                    st.caption(
                        f"{subject['Degree']} | "
                        f"{subject['Course']} | "
                        f"Semester {subject['Semester']} | "
                        f"{subject['Credits']} credits"
                    )

            else:

                st.info(
                    "No existing subject directly "
                    "covers this skill."
                )

def show_reporting():

    session = st.session_state.session

    st.title("Analytical Reports")

    st.write(
        "Generate statistics, charts and trend summaries "
        "from CROSSWALK analytics."
    )

    st.divider()

    # -----------------------------------------------------
    # SELECT REPORT
    # -----------------------------------------------------

    report_type = st.selectbox(
        "Analysis Type",
        get_report_options()
    )

    selections = get_report_selections(
        report_type
    )

    if not selections:

        st.warning(
            "Data unavailable for this report."
        )

        return

    selection = st.selectbox(
        "Select Course / Field / Industry",
        sorted(set(selections))
    )

    if st.button(
        "Generate Report",
        type="primary"
    ):

        report = build_report(
            report_type,
            selection
        )

        st.session_state.report_result = report

    # -----------------------------------------------------
    # DISPLAY REPORT
    # -----------------------------------------------------

    if "report_result" not in st.session_state:

        st.info(
            "Select an analysis and click "
            "**Generate Report**."
        )

        return

    report = st.session_state.report_result

    if not report["success"]:

        st.warning(
            report["message"]
        )

        return

    st.divider()

    st.header(
        report["analysis_type"]
    )

    st.caption(
        f"Selection: {report['selection']}"
    )

    # -----------------------------------------------------
    # STATISTICS
    # -----------------------------------------------------

    statistics = report["statistics"]

    if statistics:

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total",
                statistics["total"]
            )

        with col2:
            st.metric(
                "Average",
                statistics["average"]
            )

        with col3:
            st.metric(
                "Highest",
                statistics["highest"]["label"]
            )

        with col4:
            st.metric(
                "Lowest",
                statistics["lowest"]["label"]
            )

    # -----------------------------------------------------
    # CHART
    # -----------------------------------------------------

    st.subheader("Report Chart")

    chart_data = {
        item["label"]: item["value"]
        for item in report["data"]
    }

    st.bar_chart(chart_data)

    # -----------------------------------------------------
    # TREND SUMMARY
    # -----------------------------------------------------

    st.subheader("Trend Summary")

    st.info(
        report["trend_summary"]
    )

    # -----------------------------------------------------
    # DATA TABLE
    # -----------------------------------------------------

    st.subheader("Report Data")

    st.dataframe(
        report["data"],
        use_container_width=True
    )

def logout():

    st.session_state.logged_in = False
    st.session_state.session = None
    st.session_state.selected_career_id = None
    st.session_state.career_analysis = None

    st.rerun()


# =========================================================
# MAIN APPLICATION
# =========================================================

if not st.session_state.logged_in:

    show_login()

else:

    session = st.session_state.session

    if session["role"] == "Student":

        show_student_dashboard()

    elif session["role"] == "College/University":

        show_institutional_dashboard()

    elif session["role"] == "Curriculum Designer":

        show_curriculum_dashboard()

    else:

        st.error("Unknown user role.")