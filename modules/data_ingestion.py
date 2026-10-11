import os
import pandas as pd

from database import get_connection

# --------------------------------------------------
# Import Dataset
# --------------------------------------------------

def import_dataset(dataset):
    """
    Import an Education, Employment or Skills CSV file.
    """

    file_path = os.path.join(
        "data",
        f"{dataset.lower()}.csv"
    )

    # Check if file exists
    if not os.path.exists(file_path):
        return []

    # Read CSV
    records = pd.read_csv(file_path)

    # Check if file has no rows
    if records.empty:
        return []

    return records

# --------------------------------------------------
# Clean and Validate Records
# --------------------------------------------------

# --------------------------------------------------
# Clean and Validate Records
# --------------------------------------------------

def clean_and_validate_records(records, dataset):
    """
    Remove incomplete and duplicate records.

    Records with missing required fields are logged for review.
    """

    cleaned = []
    review_records = []

    required_fields = {
        "Education": [
            "Education_Id",
            "Degree",
            "Course",
            "Specialization",
            "College"
        ],

        "Employment": [
            "Occupation_Id",
            "Job_Title",
            "Industry",
            "Degree",
            "Course",
            "Specialization",
            "College",
            "Graduation_Year",
            "Employment_Status",
            "Experience_Level"
        ],

        "Skills": [
            "Skill_Id",
            "Skill_Name",
            "Category",
            "Domain",
            "Demand_Trend"
        ]
    }

    fields = required_fields.get(dataset, [])

    for _, record in records.iterrows():

        # Check only required fields
        missing_required_field = False

        for field in fields:
            value = record[field]

            if pd.isna(value) or str(value).strip() == "":
                missing_required_field = True
                break

        if missing_required_field:
            review_records.append({
                "record": record.to_dict(),
                "reason": "Missing required field"
            })
            continue

        # Convert row to dictionary
        record_dict = record.to_dict()

        # Check for exact duplicate
        if record_dict in cleaned:
            continue

        cleaned.append(record_dict)

    return cleaned, review_records

# --------------------------------------------------
# Find Standard Label
# --------------------------------------------------

def find_standard_label(label, label_type, mappings):
    """
    Find the standard label for a raw label.

    Returns:
        Standard label if a mapping exists.
        Original label if it is already a standard label.
        None if no match exists.
    """

    if pd.isna(label):
        return None

    label = str(label).strip()

    # First check raw-label mappings
    matching = mappings[
        (mappings["Label_Type"] == label_type) &
        (mappings["Raw_Label"].str.strip().str.lower() == label.lower())
    ]

    if not matching.empty:
        return matching.iloc[0]["Standard_Label"]

    # Check whether the label is already a standard label
    standard_matching = mappings[
        (mappings["Label_Type"] == label_type) &
        (mappings["Standard_Label"].str.strip().str.lower() == label.lower())
    ]

    if not standard_matching.empty:
        return standard_matching.iloc[0]["Standard_Label"]

    return None


# --------------------------------------------------
# Standardize Labels
# --------------------------------------------------

# --------------------------------------------------
# Standardize Labels
# --------------------------------------------------

def standardize_labels(cleaned_records, dataset):
    """
    Standardize equivalent labels using label_mappings.csv.

    Unmapped labels are sent for review, but the original
    record is retained so that data is not lost.
    """

    mappings_path = os.path.join(
        "data",
        "label_mappings.csv"
    )

    mappings = pd.read_csv(mappings_path)

    standardized = []
    review_records = []

    fields_to_standardize = {
        "Education": {
            "Degree": "Degree"
        },

        "Employment": {
            "Degree": "Degree",
            "Job_Title": "Job_Title",
            "Industry": "Industry"
        },

        "Skills": {
            "Skill_Name": "Skill"
        }
    }

    fields = fields_to_standardize.get(dataset, {})

    for record in cleaned_records:

        record_copy = record.copy()

        for field, label_type in fields.items():

            label = record_copy.get(field)

            standard = find_standard_label(
                label,
                label_type,
                mappings
            )

            if standard is None:

                review_records.append({
                    "record": record_copy,
                    "reason": f"Unmapped {label_type}: {label}"
                })

                # Keep the original label
                continue

            record_copy[field] = standard

        # Always retain the record
        standardized.append(record_copy)

    return standardized, review_records
# --------------------------------------------------
# Flag Conflicts
# --------------------------------------------------

def flag_conflicts(standardized_records):
    """
    Find records with the same ID but different data.

    Conflicting records are sent for review.
    """

    conflicts = []

    for i in range(len(standardized_records)):

        current_record = standardized_records[i]

        # Find the ID field
        if "Occupation_Id" in current_record:
            record_id = current_record["Occupation_Id"]
        elif "Education_Id" in current_record:
            record_id = current_record["Education_Id"]
        elif "Skill_Id" in current_record:
            record_id = current_record["Skill_Id"]
        else:
            continue

        # Compare with the remaining records
        for j in range(i + 1, len(standardized_records)):

            other_record = standardized_records[j]

            if "Occupation_Id" in other_record:
                other_id = other_record["Occupation_Id"]
            elif "Education_Id" in other_record:
                other_id = other_record["Education_Id"]
            elif "Skill_Id" in other_record:
                other_id = other_record["Skill_Id"]
            else:
                continue

            # Same ID
            if record_id == other_id:

                # Compare the complete records
                if current_record != other_record:

                    conflicts.append({
                        "record": current_record,
                        "other_record": other_record,
                        "reason": f"Conflicting records with ID: {record_id}"
                    })

    return conflicts

# --------------------------------------------------
# Store Standardized Data
# --------------------------------------------------

def store_standardized_data(standardized_records, dataset):
    """
    Store standardized records in the corresponding
    standardized database table.
    """

    conn = get_connection()
    cursor = conn.cursor()

    try:

        if dataset == "Education":

            for record in standardized_records:
                cursor.execute("""
                    INSERT OR REPLACE INTO standardized_education
                    (
                        Education_Id,
                        Degree,
                        Course,
                        Specialization,
                        College
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    record["Education_Id"],
                    record["Degree"],
                    record["Course"],
                    record["Specialization"],
                    record["College"]
                ))

        elif dataset == "Employment":

            for record in standardized_records:
                cursor.execute("""
                    INSERT OR REPLACE INTO standardized_employment
                    (
                        Occupation_Id,
                        Job_Title,
                        Industry,
                        Degree,
                        Course,
                        Specialization,
                        College,
                        Graduation_Year,
                        Employment_Status,
                        Experience_Level,
                        Previous_Job_Title
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    record["Occupation_Id"],
                    record["Job_Title"],
                    record["Industry"],
                    record["Degree"],
                    record["Course"],
                    record["Specialization"],
                    record["College"],
                    record["Graduation_Year"],
                    record["Employment_Status"],
                    record["Experience_Level"],
                    record["Previous_Job_Title"]
                ))

        elif dataset == "Skills":

            for record in standardized_records:
                cursor.execute("""
                    INSERT OR REPLACE INTO standardized_skills
                    (
                        Skill_Id,
                        Skill_Name,
                        Category,
                        Domain,
                        Demand_Trend
                    )
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    record["Skill_Id"],
                    record["Skill_Name"],
                    record["Category"],
                    record["Domain"],
                    record["Demand_Trend"]
                ))

        else:
            return "Unknown dataset."

        conn.commit()

        return "Stored"

    except Exception as e:
        conn.rollback()
        return f"Storage failed: {e}"

    finally:
        conn.close()