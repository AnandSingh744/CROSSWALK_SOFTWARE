"""
CROSSWALK - Career Guidance and Curriculum Intelligence System
Streamlit front end (multi-page, role based).

Pages
-----
Student              Home, My Profile, Explore Careers, Career Details,
                     Alignment, Recommendations
College/University   Institutional Analytics, Reports
Curriculum Designer  Curriculum Intelligence, Reports
"""

import html
import inspect
import itertools

import plotly.graph_objects as go
import streamlit as st

from modules.institutional_analytics import (
    get_available_fields,
    analyse_institutional_data,
)
from modules.reporting import (
    get_report_options,
    get_report_selections,
    build_report,
)
from modules.curriculum_intelligence import (
    get_curriculum_selections,
    analyse_curriculum,
)
from modules.authentication import login_user, register_user
from modules.student_profile import (
    find_student_by_user,
    save_student_profile,
    text_to_list,
)
from modules.career_exploration import (
    search_or_browse_careers,
    retrieve_career_requirements,
)
from modules.alignment_analysis import analyze_alignment
from modules.skill_gap_recommendation import analyze_skill_gap

st.set_page_config(
    page_title="CROSSWALK",
    page_icon="🎓",
    layout="wide",
)


# =========================================================
# DESIGN TOKENS
# =========================================================
# Asphalt-and-signage palette: dark ink for text, a deep teal for
# primary actions, crossing-sign yellow and a muted coral for status.

INK = "#1B2230"
TEAL = "#0F6E6E"
SIGNAL = "#E8B100"
CORAL = "#C8553D"
MIST = "#E9EEF3"
MUTED = "#5B6475"

LEVEL_COLOUR = {"High": TEAL, "Medium": SIGNAL, "Low": CORAL}
CHART_COLOURS = [TEAL, SIGNAL, CORAL, "#4C6A92", "#8FA3B8", "#7A8B6F"]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,700&family=Instrument+Sans:wght@400;500;600&display=swap');

.stApp, .stApp p, .stApp li, .stApp label,
.stApp input, .stApp textarea, .stApp button {
    font-family: 'Instrument Sans', 'Segoe UI', system-ui, sans-serif;
}
h1, h2, h3, h4 {
    font-family: 'Bricolage Grotesque', 'Segoe UI', system-ui, sans-serif !important;
    letter-spacing: -0.01em;
    color: __INK__;
}
.block-container { padding-top: 2.2rem; max-width: 1150px; }
[data-testid="stSidebar"] { border-right: 1px solid #D5DDE6; }

/* crosswalk stripe: the one brand motif */
.xwalk {
    height: 12px; width: 100%; margin-bottom: 1rem; border-radius: 2px;
    background: repeating-linear-gradient(
        90deg, __INK__ 0 26px, transparent 26px 42px);
}

/* skill chips */
.chips { display: flex; flex-wrap: wrap; gap: .4rem; margin: .25rem 0 .9rem; }
.chip {
    padding: .2rem .7rem; border-radius: 999px; font-size: .85rem;
    font-weight: 500; border: 1px solid transparent;
}
.chip-match   { background: #DCEFEC; color: #0B4F4F; border-color: #B7DAD5; }
.chip-miss    { background: #F8E3DC; color: #8A3320; border-color: #EBC3B7; }
.chip-neutral { background: __MIST__; color: __INK__; border-color: #D5DDE6; }

/* alignment level pill */
.pill {
    display: inline-block; padding: .25rem .8rem; border-radius: 6px;
    font-weight: 600; font-size: .9rem;
}
.pill-high   { background: #DCEFEC; color: #0B4F4F; }
.pill-medium { background: #FBEFC0; color: #6B5200; }
.pill-low    { background: #F8E3DC; color: #8A3320; }

[data-testid="stMetric"] {
    border: 1px solid #D5DDE6; border-radius: 10px; padding: .6rem .9rem;
}
</style>
"""


def inject_css():
    css = (
        CSS.replace("__INK__", INK)
        .replace("__MIST__", MIST)
    )
    st.markdown(css, unsafe_allow_html=True)


# =========================================================
# STREAMLIT VERSION COMPATIBILITY
# =========================================================
# Newer Streamlit versions use width="stretch"; older ones use
# use_container_width=True. Pick whichever this install supports.

def _stretch(func):
    try:
        params = inspect.signature(func).parameters
    except (TypeError, ValueError):
        return {}
    if "width" in params:
        return {"width": "stretch"}
    if "use_container_width" in params:
        return {"use_container_width": True}
    return {}


BTN_FULL = _stretch(st.button)
CHART_FULL = _stretch(st.plotly_chart)
TABLE_FULL = _stretch(st.dataframe)

_figure_ids = itertools.count()


def show_figure(fig):
    st.plotly_chart(fig, key=f"fig_{next(_figure_ids)}", **CHART_FULL)


# =========================================================
# SESSION STATE
# =========================================================

SESSION_DEFAULTS = {
    "logged_in": False,
    "session": None,
    "selected_career_id": None,
    "career_analysis": None,
    "institutional_analysis": None,
    "curriculum_analysis": None,
    "report_result": None,
    "career_limit": 12,
}


def init_state():
    for key, value in SESSION_DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def logout():
    """Clear everything, so the next login starts clean."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


# =========================================================
# SMALL HELPERS
# =========================================================

PAGES = {}  # filled in by build_pages(); used for page-to-page navigation

STUDENT_COLUMNS = [
    "student_id", "user_id", "degree", "course", "specialization",
    "college", "technical_skills", "soft_skills", "certifications",
    "interests", "industries", "preferences", "status",
]


def go_to(key):
    st.switch_page(PAGES[key])


def esc(value):
    """HTML-escape anything that goes into unsafe_allow_html markup."""
    return html.escape("" if value is None else str(value))


def pct(value):
    return f"{(value or 0) * 100:.0f}%"


def pipes_to_commas(value):
    return (value or "").replace("|", ", ")


def load_student():
    """Student row as a dict (same column order as find_student_by_user)."""
    row = find_student_by_user(st.session_state.session["user_id"])
    return dict(zip(STUDENT_COLUMNS, row)) if row else None


def profile_readiness(student):
    """Is the profile filled in enough for an analysis to mean anything?"""
    if not (student["degree"] and student["course"]):
        return False, (
            "Add your degree and course so your education can be "
            "compared with the career."
        )
    if not (student["technical_skills"] or student["soft_skills"]):
        return False, (
            "Add at least one technical or soft skill so your skills "
            "can be compared with the career."
        )
    return True, ""


def chips_html(items, kind="neutral"):
    spans = "".join(
        f'<span class="chip chip-{kind}">{esc(item)}</span>'
        for item in items
    )
    return f'<div class="chips">{spans}</div>'


def show_chips(items, kind="neutral", empty_text="None"):
    if items:
        st.markdown(chips_html(items, kind), unsafe_allow_html=True)
    else:
        st.caption(empty_text)


def empty_state(message, button_label, target):
    st.info(message)
    if st.button(button_label, key=f"empty_to_{target}"):
        go_to(target)


# =========================================================
# CHARTS
# =========================================================

def style_figure(fig, height=300):
    fig.update_layout(
        height=height,
        margin=dict(l=10, r=10, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=INK, family="Instrument Sans, sans-serif"),
    )
    return fig


def score_gauge(score, level):
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "%", "font": {"size": 54}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1},
                "bar": {
                    "color": LEVEL_COLOUR.get(level, TEAL),
                    "thickness": 0.28,
                },
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 40], "color": "#F3DCD5"},
                    {"range": [40, 70], "color": "#F6E9B8"},
                    {"range": [70, 100], "color": "#CFE6E3"},
                ],
            },
        )
    )
    return style_figure(fig, 260)


def match_radar(education, skills, interests):
    labels = ["Education", "Skills", "Interests"]
    values = [education, skills, interests]
    fig = go.Figure(
        go.Scatterpolar(
            r=values + values[:1],
            theta=labels + labels[:1],
            fill="toself",
            line=dict(color=TEAL),
            fillcolor="rgba(15,110,110,0.25)",
        )
    )
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                range=[0, 1],
                tickvals=[0, 0.5, 1],
                ticktext=["0", "50%", "100%"],
            )
        ),
        showlegend=False,
    )
    return style_figure(fig, 260)


def bar_figure(labels, values, horizontal=False, colour=TEAL):
    labels = [str(label) for label in labels]
    if horizontal:
        fig = go.Figure(
            go.Bar(x=values, y=labels, orientation="h", marker_color=colour)
        )
        fig.update_yaxes(autorange="reversed")
    else:
        fig = go.Figure(go.Bar(x=labels, y=values, marker_color=colour))
    height = max(260, 34 * len(labels) + 80) if horizontal else 320
    return style_figure(fig, height)


def donut_figure(labels, values):
    fig = go.Figure(
        go.Pie(
            labels=list(labels),
            values=list(values),
            hole=0.55,
            marker=dict(colors=CHART_COLOURS),
        )
    )
    return style_figure(fig, 260)


# =========================================================
# LOGIN AND SIGN UP
# =========================================================

def show_login():
    _, centre, _ = st.columns([1, 1.25, 1])

    with centre:
        st.markdown('<div class="xwalk"></div>', unsafe_allow_html=True)
        st.title("CROSSWALK")
        st.caption("Career guidance and curriculum intelligence")

        login_tab, signup_tab = st.tabs(["Log in", "Create account"])

        with login_tab:
            with st.form("login_form"):
                email = st.text_input("Email", key="login_email")
                password = st.text_input(
                    "Password", type="password", key="login_password"
                )
                submitted = st.form_submit_button(
                    "Log in", type="primary", **BTN_FULL
                )

            if submitted:
                if not email or not password:
                    st.error("Please enter both email and password.")
                else:
                    result = login_user(email, password)
                    if result["success"]:
                        st.session_state.logged_in = True
                        st.session_state.session = result["session"]
                        st.rerun()
                    else:
                        st.error(result["message"])

        with signup_tab:
            st.caption("Student accounts only. Institution and curriculum "
                       "accounts are created by an administrator.")
            with st.form("signup_form"):
                new_name = st.text_input("Full name", key="signup_name")
                new_email = st.text_input("Email", key="signup_email")
                new_password = st.text_input(
                    "Password (8+ characters)",
                    type="password",
                    key="signup_password",
                )
                confirm = st.text_input(
                    "Confirm password",
                    type="password",
                    key="signup_confirm",
                )
                created = st.form_submit_button(
                    "Create account", type="primary", **BTN_FULL
                )

            if created:
                if new_password != confirm:
                    st.error("Passwords do not match.")
                else:
                    result = register_user(
                        new_name, new_email, new_password, "Student"
                    )
                    if result["success"]:
                        st.success(result["message"])
                    else:
                        st.error(result["message"])


# =========================================================
# STUDENT PAGES
# =========================================================

def page_home():
    student = load_student()
    session = st.session_state.session
    first_name = (session.get("name") or "there").split()[0]

    st.title(f"Welcome, {first_name}")
    st.caption("Four steps from your profile to a plan for the skills you are missing.")

    profile_done = bool(student and student["status"] == "Complete")
    career_done = st.session_state.selected_career_id is not None
    analysis_done = st.session_state.career_analysis is not None

    steps = [
        ("Build your profile", profile_done, "profile",
         "Education, skills and interests."),
        ("Choose a career", career_done, "explore",
         "Search roles and pick one to aim for."),
        ("Check your alignment", analysis_done, "alignment",
         "See how your profile matches the role."),
        ("Close your gaps", analysis_done, "recommendations",
         "Courses for the skills you are missing."),
    ]

    columns = st.columns(len(steps))
    for index, (column, (title, done, target, blurb)) in enumerate(
        zip(columns, steps), start=1
    ):
        with column:
            with st.container(border=True):
                st.markdown(f"**{index}. {title}**")
                st.caption(blurb)
                st.write("Done" if done else "Not started")
                if st.button("Open", key=f"home_step_{index}"):
                    go_to(target)

    st.write("")
    next_step = next((s for s in steps if not s[1]), None)
    if next_step:
        if st.button(f"Continue: {next_step[0]}", type="primary"):
            go_to(next_step[2])
    else:
        st.success("You have completed every step. Pick another career to compare.")


def page_profile():
    st.title("My profile")
    st.caption("Your education, skills and interests drive every career match.")

    student = load_student()
    if student is None:
        st.error("Student profile could not be found.")
        return

    if student["status"] == "Complete":
        st.success("Profile status: Complete")
    else:
        st.warning("Profile status: Incomplete. Add your skills and interests.")

    with st.form("profile_form"):
        st.subheader("Education")
        left, right = st.columns(2)
        degree = left.text_input("Degree", value=student["degree"] or "")
        course = right.text_input("Course", value=student["course"] or "")
        specialization = left.text_input(
            "Specialization", value=student["specialization"] or ""
        )
        college = right.text_input("College", value=student["college"] or "")

        st.subheader("Skills")
        technical = st.text_area(
            "Technical skills",
            value=pipes_to_commas(student["technical_skills"]),
            help="Example: Python, SQL, Pandas",
        )
        soft = st.text_area(
            "Soft skills",
            value=pipes_to_commas(student["soft_skills"]),
            help="Example: Communication, Leadership",
        )
        certifications = st.text_area(
            "Certifications",
            value=pipes_to_commas(student["certifications"]),
        )

        st.subheader("Career interests")
        interests = st.text_area(
            "Areas of interest",
            value=pipes_to_commas(student["interests"]),
            help="Example: Artificial Intelligence, Data Science",
        )
        industries = st.text_area(
            "Preferred industries",
            value=pipes_to_commas(student["industries"]),
            help="Example: Technology, Finance",
        )
        preferences = st.text_area(
            "Career preferences",
            value=pipes_to_commas(student["preferences"]),
            help="Example: Data Scientist, ML Engineer",
        )

        saved = st.form_submit_button("Save profile", type="primary")

    if saved:
        result = save_student_profile(
            student_id=student["student_id"],
            degree=degree,
            course=course,
            specialization=specialization,
            college=college,
            technical_skills=text_to_list(technical),
            soft_skills=text_to_list(soft),
            certifications=text_to_list(certifications),
            areas_of_interest=text_to_list(interests),
            preferred_industries=text_to_list(industries),
            career_preferences=text_to_list(preferences),
        )

        if result["success"]:
            st.success(result["message"])
            if result["profile_status"] == "Complete":
                st.success("Profile status: Complete")
            else:
                st.warning(
                    "Profile status: Incomplete. "
                    "Please add your skills and interests."
                )
        else:
            st.error(result["message"])


def page_explore():
    st.title("Explore careers")
    st.caption("Search by job title or industry, then select a career to look at.")

    all_careers = search_or_browse_careers()
    industries = sorted({c[2] for c in all_careers if c[2]})

    left, right = st.columns([2, 1])
    term = left.text_input(
        "Search",
        placeholder="Data, Engineer, Analyst",
        key="career_search",
    )
    industry = right.selectbox(
        "Industry", ["All industries"] + industries, key="career_industry"
    )

    careers = search_or_browse_careers(search_term=term)
    if industry != "All industries":
        careers = [
            c for c in careers
            if (c[2] or "").lower() == industry.lower()
        ]

    if not careers:
        st.info("No matching careers were found.")
        return

    limit = st.session_state.career_limit
    st.write(f"**{len(careers)} careers found**")

    for career in careers[:limit]:
        occupation_id, job_title, career_industry, degree, course, spec = career

        with st.container(border=True):
            info, action = st.columns([5, 1])
            with info:
                st.markdown(f"**{job_title}**")
                st.caption(career_industry or "Industry not specified")
                st.caption(
                    ", ".join(
                        part for part in (degree, course, spec) if part
                    ) or "Any degree"
                )
            with action:
                if st.button("Select", key=f"select_{occupation_id}"):
                    st.session_state.selected_career_id = occupation_id
                    st.session_state.career_analysis = None
                    go_to("details")

    if len(careers) > limit:
        if st.button(f"Show more ({len(careers) - limit} left)"):
            st.session_state.career_limit = limit + 12
            st.rerun()


def page_details():
    st.title("Career details")

    selected_id = st.session_state.selected_career_id
    if not selected_id:
        empty_state("You have not selected a career yet.", "Browse careers", "explore")
        return

    career = retrieve_career_requirements(selected_id)
    if not career:
        st.error("Career requirements are unavailable.")
        return

    st.header(career["Job_Title"])
    st.caption(career["Industry"] or "Industry not specified")

    left, right = st.columns(2)
    with left:
        st.subheader("Education")
        st.write(f"**Degree:** {career['Degree_Mapping'] or 'Not specified'}")
        st.write(f"**Course:** {career['Course'] or 'Not specified'}")
        st.write(f"**Specialization:** {career['Specialization'] or 'Not specified'}")
    with right:
        st.subheader("Required skills")
        show_chips(
            career["Required_Skills"],
            "neutral",
            "No required skills available.",
        )

    st.divider()

    student = load_student()
    if student is None:
        st.error("Student profile could not be found.")
        return

    ready, message = profile_readiness(student)
    if not ready:
        st.warning(message)
        if st.button("Update my profile", key="details_to_profile"):
            go_to("profile")
        return

    if student["status"] != "Complete":
        st.info(
            "Your profile is incomplete, so the result may look lower "
            "than it should."
        )

    if st.button("Analyze my alignment", type="primary"):
        st.session_state.career_analysis = {
            "alignment": analyze_alignment(student["student_id"], selected_id),
            "skill_gap": analyze_skill_gap(student["student_id"], selected_id),
        }
        go_to("alignment")


def page_alignment():
    st.title("Alignment")

    data = st.session_state.career_analysis
    if not data:
        empty_state(
            "Choose a career and run the analysis first.",
            "Browse careers",
            "explore",
        )
        return

    alignment = data["alignment"]
    if not alignment["success"]:
        st.error(alignment["message"])
        return

    career = alignment["career"]
    score = alignment["alignment_percentage"]
    level = alignment["classification"]
    education = alignment["education_match"]
    skills = alignment["skill_match"]
    interests = alignment["interest_match"]

    st.subheader(career["job_title"])
    st.caption(career["industry"] or "Industry not specified")

    gauge_col, radar_col = st.columns([1.1, 1])
    with gauge_col:
        show_figure(score_gauge(score, level))
        st.markdown(
            f'<span class="pill pill-{esc(level.lower())}">'
            f"{esc(level)} alignment</span>",
            unsafe_allow_html=True,
        )
        st.caption("Score = 40% education + 40% skills + 20% interests.")
    with radar_col:
        show_figure(
            match_radar(education["score"], skills["score"], interests["score"])
        )

    m1, m2, m3 = st.columns(3)
    m1.metric("Education", pct(education["score"]))
    m2.metric("Skills", pct(skills["score"]))
    m3.metric("Interests", pct(interests["score"]))

    matched = skills["matched_skills"]
    missing = skills["missing_skills"]

    st.subheader("Skills")
    st.caption(f"{len(matched)} of {len(matched) + len(missing)} required skills matched")

    have, lack = st.columns(2)
    with have:
        st.write("**You have**")
        show_chips(matched, "match", "No required skills matched yet.")
    with lack:
        st.write("**Still missing**")
        if missing:
            show_chips(missing, "miss")
        else:
            st.success("No missing required skills.")

    st.divider()
    if st.button("See recommendations", type="primary"):
        go_to("recommendations")


def page_recommendations():
    st.title("Recommendations")

    data = st.session_state.career_analysis
    if not data:
        empty_state(
            "Choose a career and run the analysis first.",
            "Browse careers",
            "explore",
        )
        return

    alignment = data["alignment"]
    gap = data["skill_gap"]

    if alignment["success"]:
        st.caption(
            f"For {alignment['career']['job_title']}, "
            f"{alignment['career']['industry'] or 'industry not specified'}"
        )

    if not gap["success"]:
        st.info(gap["message"])
        return

    if not gap["missing_skills"]:
        st.success("You already have every required skill for this career.")
        return

    technical = gap["gaps"]["Technical_Gaps"]
    soft = gap["gaps"]["Soft_Gaps"]

    st.subheader("Skill gaps")
    left, right = st.columns(2)
    with left:
        st.write("**Technical**")
        show_chips(technical, "miss", "None")
    with right:
        st.write("**Soft skills**")
        show_chips(soft, "miss", "None")

    st.subheader("Recommended courses")
    recommendations = gap["recommendations"]

    if not recommendations:
        st.info("No course recommendations available.")
    else:
        def course_card(course):
            with st.container(border=True):
                st.markdown(f"**{course['Course_Name']}**")
                st.caption(
                    f"{course['Level']}, {course['Duration_Weeks']} weeks, "
                    f"covers {course['Relevance']} of your gaps"
                )
                show_chips(course["Covered_Skills"], "match")

        for course in recommendations[:6]:
            course_card(course)

        if len(recommendations) > 6:
            with st.expander(f"{len(recommendations) - 6} more courses"):
                for course in recommendations[6:]:
                    course_card(course)

    uncovered = gap["uncovered_skills"]
    if uncovered:
        st.warning(
            "No available course was found for: " + ", ".join(uncovered)
        )


# =========================================================
# COLLEGE / UNIVERSITY PAGES
# =========================================================

def page_institution():
    st.title("Institutional analytics")
    st.caption(
        "Course demand, employment outcomes and education-career trends."
    )

    fields = get_available_fields()
    if not fields:
        st.warning(
            "Data unavailable: no education fields are available for analysis."
        )
        return

    selected_field = st.selectbox("Course or specialization", fields)

    if st.button("Analyse", type="primary"):
        st.session_state.institutional_analysis = analyse_institutional_data(
            selected_field
        )

    result = st.session_state.institutional_analysis
    if result is None:
        st.info("Select a course or field and click **Analyse**.")
        return

    if not result["success"]:
        st.warning(result["message"])
        return

    st.header(result["selection"])

    demand = result["demand_stats"]
    paths = result["career_paths"]
    mismatches = result["mismatch_patterns"]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Education records", len(result["courses"]))
    m2.metric("Career records", sum(d["Career_Count"] for d in demand))
    m3.metric("Career paths", len(paths))
    m4.metric("Mismatches", len(mismatches))

    demand_tab, outcomes_tab, paths_tab, mismatch_tab = st.tabs(
        ["Demand", "Outcomes", "Career paths", "Mismatches"]
    )

    with demand_tab:
        if demand:
            labels = [
                f"{d['Degree']}, {d['Specialization'] or d['Course']}"
                for d in demand
            ]
            show_figure(
                bar_figure(
                    labels,
                    [d["Career_Count"] for d in demand],
                    horizontal=True,
                )
            )
        else:
            st.info("Data unavailable.")

    with outcomes_tab:
        outcomes = result["outcome_stats"]
        if not outcomes:
            st.info("Employment outcome data unavailable.")
        for index, outcome in enumerate(outcomes):
            with st.expander(
                f"{outcome['Degree']}, {outcome['Course']}",
                expanded=(index == 0),
            ):
                statuses = outcome["Employment_Status"]
                experience = outcome["Experience_Level"]

                if statuses or experience:
                    left, right = st.columns(2)
                    with left:
                        st.write("**Employment status**")
                        if statuses:
                            show_figure(
                                donut_figure(statuses.keys(), statuses.values())
                            )
                        else:
                            st.info("Unavailable.")
                    with right:
                        st.write("**Experience level**")
                        if experience:
                            show_figure(
                                bar_figure(
                                    list(experience.keys()),
                                    list(experience.values()),
                                )
                            )
                        else:
                            st.info("Unavailable.")
                else:
                    st.info("Employment outcome data unavailable.")

                st.caption("Salary information: " + outcome["Salary"])

    with paths_tab:
        if paths:
            top = paths[:10]
            show_figure(
                bar_figure(
                    [p["Career"] for p in top],
                    [p["Count"] for p in top],
                    horizontal=True,
                )
            )
        else:
            st.info("Career path data unavailable.")

    with mismatch_tab:
        if mismatches:
            st.warning(
                f"{len(mismatches)} education record(s) have no mapped career."
            )
            for mismatch in mismatches:
                st.write(
                    f"**{mismatch['Degree']}**, {mismatch['Course']}, "
                    f"{mismatch['Specialization']}"
                )
                st.caption(mismatch["Issue"])
        else:
            st.success("No education-career mismatches were found.")


# =========================================================
# CURRICULUM DESIGNER PAGES
# =========================================================

def page_curriculum():
    st.title("Curriculum intelligence")
    st.caption(
        "Find rising industry skills and compare them with the curriculum."
    )

    industries, careers = get_curriculum_selections()

    selection_type = st.radio(
        "Analyse by", ["Industry", "Career"], horizontal=True
    )

    options = industries if selection_type == "Industry" else careers
    if not options:
        st.warning(f"{selection_type} data unavailable.")
        return

    selection = st.selectbox(selection_type, options)

    if st.button("Analyse curriculum", type="primary"):
        st.session_state.curriculum_analysis = analyse_curriculum(
            selection_type, selection
        )

    result = st.session_state.curriculum_analysis
    if result is None:
        st.info("Select an industry or career and click **Analyse curriculum**.")
        return

    if not result["success"]:
        st.warning(result["message"])
        return

    st.header(result["selection"])

    trending = result["trending_skills"]
    gaps = result["gaps"]
    careers_found = result["careers"]

    m1, m2, m3 = st.columns(3)
    m1.metric("Related careers", len({c["Job_Title"] for c in careers_found}))
    m2.metric("Rising skills", len(trending))
    m3.metric("Curriculum gaps", len(gaps))

    overview_tab, gaps_tab = st.tabs(["Overview", "Gaps and subjects"])

    with overview_tab:
        st.subheader("Related careers")
        show_chips(
            sorted({c["Job_Title"] for c in careers_found}),
            "neutral",
        )

        st.subheader("Trending industry skills")
        gap_names = {g["Skill_Name"] for g in gaps}
        covered = [s["Skill_Name"] for s in trending if s["Skill_Name"] not in gap_names]
        st.write("**Missing from the curriculum**")
        show_chips(sorted(gap_names), "miss", "None")
        st.write("**Already covered**")
        show_chips(sorted(covered), "match", "None")

    with gaps_tab:
        if not gaps:
            st.success("Curriculum already covers the trending skills.")
            return

        st.subheader("Recommended subjects")
        st.caption("Existing subjects that already teach each missing skill.")

        for recommendation in result["recommendations"]:
            with st.expander(recommendation["Skill"]):
                subjects = recommendation["Subjects"]
                if subjects:
                    for subject in subjects:
                        st.write(f"**{subject['Subject_Name']}**")
                        st.caption(
                            f"{subject['Degree']}, {subject['Course']}, "
                            f"semester {subject['Semester']}, "
                            f"{subject['Credits']} credits"
                        )
                else:
                    st.info("No existing subject directly covers this skill.")


# =========================================================
# REPORTS (College/University and Curriculum Designer)
# =========================================================

def page_reports():
    st.title("Analytical reports")
    st.caption("Statistics, charts and trend summaries from CROSSWALK analytics.")

    report_type = st.selectbox("Analysis type", get_report_options())
    selections = get_report_selections(report_type)

    if not selections:
        st.warning("Data unavailable for this report.")
        return

    selection = st.selectbox(
        "Course, field or industry", sorted(set(selections))
    )

    if st.button("Generate report", type="primary"):
        st.session_state.report_result = build_report(report_type, selection)

    report = st.session_state.report_result
    if report is None:
        st.info("Select an analysis and click **Generate report**.")
        return

    if not report["success"]:
        st.warning(report["message"])
        return

    st.header(report["analysis_type"])
    st.caption(f"Selection: {report['selection']}")

    statistics = report["statistics"]
    if statistics:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", statistics["total"])
        c2.metric("Average", statistics["average"])
        with c3:
            st.metric("Highest", statistics["highest"]["value"])
            st.caption(statistics["highest"]["label"])
        with c4:
            st.metric("Lowest", statistics["lowest"]["value"])
            st.caption(statistics["lowest"]["label"])

    chart_tab, summary_tab, data_tab = st.tabs(["Chart", "Summary", "Data"])

    with chart_tab:
        data = report["data"]
        if data:
            show_figure(
                bar_figure(
                    [item["label"] for item in data],
                    [item["value"] for item in data],
                    horizontal=True,
                )
            )
        else:
            st.info("No chart data available.")

    with summary_tab:
        st.info(report["trend_summary"])

    with data_tab:
        st.dataframe(report["data"], hide_index=True, **TABLE_FULL)


# =========================================================
# NAVIGATION
# =========================================================

def build_pages(role):
    """Create the page list for a role and register pages for go_to()."""
    PAGES.clear()

    if role == "Student":
        PAGES.update(
            home=st.Page(page_home, title="Home", icon="🏠", default=True),
            profile=st.Page(page_profile, title="My profile", icon="👤", url_path="profile"),
            explore=st.Page(page_explore, title="Explore careers", icon="🔍", url_path="explore"),
            details=st.Page(page_details, title="Career details", icon="📋", url_path="career"),
            alignment=st.Page(page_alignment, title="Alignment", icon="🎯", url_path="alignment"),
            recommendations=st.Page(page_recommendations, title="Recommendations", icon="📚", url_path="recommendations"),
        )
    elif role == "College/University":
        PAGES.update(
            analytics=st.Page(page_institution, title="Institutional analytics", icon="📊", default=True),
            reports=st.Page(page_reports, title="Reports", icon="📄", url_path="reports"),
        )
    elif role == "Curriculum Designer":
        PAGES.update(
            curriculum=st.Page(page_curriculum, title="Curriculum intelligence", icon="🧭", default=True),
            reports=st.Page(page_reports, title="Reports", icon="📄", url_path="reports"),
        )

    return list(PAGES.values())


# =========================================================
# MAIN APPLICATION
# =========================================================

init_state()
inject_css()

if not st.session_state.logged_in:
    show_login()
else:
    session = st.session_state.session
    pages = build_pages(session["role"])

    with st.sidebar:
        st.markdown('<div class="xwalk"></div>', unsafe_allow_html=True)
        st.write(f"**{session['name']}**")
        st.caption(session["role"])
        if st.button("Log out", key="logout_button"):
            logout()

    if not pages:
        st.error("Your account role is not recognised. Please contact an administrator.")
        st.stop()

    st.navigation(pages).run()
