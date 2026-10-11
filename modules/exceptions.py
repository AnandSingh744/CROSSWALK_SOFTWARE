from datetime import datetime
from database import get_connection


# =========================================================
# DATABASE SETUP
# =========================================================

def initialize_review_queue():

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS review_queue (
                Review_Id INTEGER PRIMARY KEY AUTOINCREMENT,
                Event_Type TEXT NOT NULL,
                Details TEXT,
                Record_1 TEXT,
                Record_2 TEXT,
                Created_At TEXT NOT NULL,
                Status TEXT NOT NULL
            )
        """)

        conn.commit()

    finally:
        conn.close()


initialize_review_queue()


# =========================================================
# USER-FACING MESSAGES
# =========================================================

def prompt_complete_required_fields():

    return "Please complete all required fields to continue"


def return_invalid_login_error():

    return "Invalid email or password"


def return_duplicate_registration_error():

    return "An account with this email already exists"


def flag_insufficient_data():

    return "Insufficient data is available for this request"


def flag_data_unavailable():

    return "Data unavailable"


def return_error(text):

    return text


# =========================================================
# LOG UNMAPPED / INCONSISTENT RECORD
# =========================================================

def log_for_review(details):

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO review_queue
            (
                Event_Type,
                Details,
                Created_At,
                Status
            )
            VALUES (?, ?, ?, ?)
        """, (
            "Unmapped record",
            str(details),
            timestamp,
            "Pending"
        ))

        conn.commit()

        return "Logged for review"

    finally:

        conn.close()


# =========================================================
# LOG CONFLICTING RECORDS
# =========================================================

def log_conflicting_records(record1, record2):

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO review_queue
            (
                Event_Type,
                Details,
                Record_1,
                Record_2,
                Created_At,
                Status
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "Conflicting records",
            "Conflict",
            str(record1),
            str(record2),
            timestamp,
            "Pending"
        ))

        conn.commit()

        return "Conflict logged for review"

    finally:

        conn.close()


# =========================================================
# LOW CONFIDENCE
# =========================================================

def label_low_confidence(result):

    if isinstance(result, dict):

        result = result.copy()

        result["confidence_label"] = (
            "Low confidence: based on limited data"
        )

        return result

    return {
        "result": result,
        "confidence_label": (
            "Low confidence: based on limited data"
        )
    }


# =========================================================
# LIST PENDING REVIEWS
# =========================================================

def list_pending_reviews():

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                Review_Id,
                Event_Type,
                Details,
                Record_1,
                Record_2,
                Created_At,
                Status
            FROM review_queue
            WHERE Status = 'Pending'
            ORDER BY Review_Id
        """)

        rows = cursor.fetchall()

    finally:

        conn.close()


    reviews = []

    for row in rows:

        reviews.append({
            "Review_Id": row[0],
            "Event_Type": row[1],
            "Details": row[2],
            "Record_1": row[3],
            "Record_2": row[4],
            "Created_At": row[5],
            "Status": row[6]
        })

    return reviews


# =========================================================
# MAIN PROCESS
# =========================================================

def handle_exception(event_type, details=None):

    if event_type == "Incomplete profile":

        return prompt_complete_required_fields()


    elif event_type == "Invalid login":

        return return_invalid_login_error()


    elif event_type == "Duplicate registration":

        return return_duplicate_registration_error()


    elif event_type == "Insufficient data":

        return flag_insufficient_data()


    elif event_type == "Data unavailable":

        return flag_data_unavailable()


    elif event_type == "Conflicting records":

        if details is None:

            return "Conflict details unavailable"

        record1 = details.get("record1")
        record2 = details.get("record2")

        return log_conflicting_records(
            record1,
            record2
        )


    elif event_type == "Unmapped record":

        return log_for_review(details)


    elif event_type == "Low confidence":

        return label_low_confidence(details)


    else:

        return return_error("Unknown event")