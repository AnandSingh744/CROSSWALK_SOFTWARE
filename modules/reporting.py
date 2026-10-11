from modules.institutional_analytics import (
    analyse_institutional_data,
    get_available_fields
)

from modules.curriculum_intelligence import (
    analyse_curriculum,
    get_curriculum_selections
)


def generate_statistics(data):
    """
    Generate total, average, highest and lowest
    from label-value pairs.
    """

    if not data:
        return None

    values = [
        item["value"]
        for item in data
        if isinstance(item["value"], (int, float))
    ]

    if not values:
        return None

    total = sum(values)
    average = total / len(values)

    highest = max(
        data,
        key=lambda item: item["value"]
    )

    lowest = min(
        data,
        key=lambda item: item["value"]
    )

    return {
        "total": total,
        "average": round(average, 2),
        "highest": highest,
        "lowest": lowest
    }


def build_report(analysis_type, selection):
    """
    Main Module 10 process.
    """

    if not analysis_type or not selection:
        return {
            "success": False,
            "message": "No analysis selected."
        }

    data = []
    trend_summary = ""

    # =====================================================
    # MODULE 8 REPORTS
    # =====================================================

    if analysis_type in [
        "Course Demand and Outcomes",
        "Education-Career Trends"
    ]:

        result = analyse_institutional_data(
            selection
        )

        if not result["success"]:
            return {
                "success": False,
                "message": result["message"]
            }

        if analysis_type == "Course Demand and Outcomes":

            for item in result["demand_stats"]:

                label = (
                    f"{item['Degree']} - "
                    f"{item['Course']}"
                )

                data.append({
                    "label": label,
                    "value": item["Career_Count"]
                })

            trend_summary = (
                f"{result['selection']} has "
                f"{len(result['courses'])} education "
                f"record(s) linked to "
                f"{sum(item['Career_Count'] for item in result['demand_stats'])} "
                f"career record(s)."
            )

        else:

            for item in result["career_paths"][:10]:

                data.append({
                    "label": item["Career"],
                    "value": item["Count"]
                })

            trend_summary = (
                f"The analysis identifies "
                f"{len(result['career_paths'])} "
                f"career path(s) associated with "
                f"{result['selection']}."
            )

    # =====================================================
    # MODULE 9 REPORTS
    # =====================================================

    elif analysis_type in [
        "Industry Skill Requirements",
        "Curriculum Recommendations"
    ]:

        result = analyse_curriculum(
            "Industry",
            selection
        )

        if not result["success"]:

            # If the selection is actually a career,
            # try career-based analysis.
            result = analyse_curriculum(
                "Career",
                selection
            )

        if not result["success"]:
            return {
                "success": False,
                "message": result["message"]
            }

        if analysis_type == "Industry Skill Requirements":

            for skill in result["trending_skills"]:

                data.append({
                    "label": skill["Skill_Name"],
                    "value": 1
                })

            trend_summary = (
                f"{len(result['trending_skills'])} "
                f"rising skill(s) were identified for "
                f"{result['selection']}."
            )

        else:

            for gap in result["gaps"]:

                data.append({
                    "label": gap["Skill_Name"],
                    "value": 1
                })

            trend_summary = (
                f"{len(result['gaps'])} "
                f"curriculum gap(s) were identified "
                f"for {result['selection']}."
            )

    else:

        return {
            "success": False,
            "message": "Invalid analysis type."
        }

    if not data:

        return {
            "success": False,
            "message": "Data unavailable."
        }

    statistics = generate_statistics(data)

    return {
        "success": True,
        "analysis_type": analysis_type,
        "selection": selection,
        "data": data,
        "statistics": statistics,
        "trend_summary": trend_summary
    }


def get_report_options():

    return [
        "Course Demand and Outcomes",
        "Education-Career Trends",
        "Industry Skill Requirements",
        "Curriculum Recommendations"
    ]


def get_report_selections(analysis_type):

    # Reports based on institutional / education data
    if analysis_type in [
        "Course Demand and Outcomes",
        "Education-Career Trends"
    ]:
        fields = get_available_fields()
        return fields

    # Reports based on industry / curriculum intelligence
    if analysis_type in [
        "Industry Skill Requirements",
        "Curriculum Recommendations"
    ]:
        industries, _ = get_curriculum_selections()
        return industries

    return []