import hashlib
import secrets

from database import get_connection


# --------------------------------------------------
# Password Hashing
# --------------------------------------------------

def hash_password(password):
    """Convert a password into a SHA-256 hash."""
    return hashlib.sha256(password.encode()).hexdigest()


# --------------------------------------------------
# Find Account
# --------------------------------------------------

def find_account(email):
    """Find a user account using their email."""

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT User_Id, Name, Email, Password_Hash, Role
            FROM users
            WHERE LOWER(Email) = LOWER(?)
            """,
            (email.strip(),)
        )

        return cursor.fetchone()

    finally:
        conn.close()


# --------------------------------------------------
# Register User
# --------------------------------------------------

def register_user(name, email, password, role="Student"):
    """
    Register a new account.

    For students, an empty (Incomplete) student profile row is created
    in the same transaction, so the Student Dashboard works immediately.

    Returns: {"success": bool, "message": str}
    """

    name = (name or "").strip()
    email = (email or "").strip()

    if not name or not email or not password or not role:
        return {"success": False, "message": "Please complete all required fields."}

    if "@" not in email or "." not in email.split("@")[-1]:
        return {"success": False, "message": "Please enter a valid email address."}

    if len(password) < 8:
        return {"success": False, "message": "Password must be at least 8 characters."}

    if find_account(email) is not None:
        return {"success": False, "message": "An account with this email already exists."}

    conn = get_connection()

    try:
        cursor = conn.cursor()

        # Next User_Id
        cursor.execute("SELECT User_Id FROM users ORDER BY User_Id DESC LIMIT 1")
        last_user = cursor.fetchone()
        next_user_no = int(last_user[0].replace("USR", "")) + 1 if last_user else 1
        user_id = f"USR{next_user_no:03d}"

        cursor.execute(
            """
            INSERT INTO users (User_Id, Name, Email, Password_Hash, Role)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, name, email, hash_password(password), role)
        )

        # Students also need a profile row
        if role == "Student":
            cursor.execute("SELECT Student_Id FROM students ORDER BY Student_Id DESC LIMIT 1")
            last_student = cursor.fetchone()
            next_student_no = int(last_student[0].replace("STU", "")) + 1 if last_student else 1
            student_id = f"STU{next_student_no:03d}"

            cursor.execute(
                """
                INSERT INTO students (Student_Id, User_Id, Profile_Status)
                VALUES (?, ?, 'Incomplete')
                """,
                (student_id, user_id)
            )

        conn.commit()
        return {"success": True, "message": "Account created. You can now log in."}

    except Exception as e:
        conn.rollback()
        return {"success": False, "message": f"Registration failed: {e}"}

    finally:
        conn.close()


# --------------------------------------------------
# Role-Based Dashboard
# --------------------------------------------------

def route_to_role_dashboard(role):
    """Return the dashboard associated with the user's role."""

    if role == "Student":
        return "Student Dashboard"

    elif role == "College/University":
        return "Institutional Analytics View"

    elif role == "Curriculum Designer":
        return "Curriculum Intelligence View"

    else:
        return "Unknown role"


# --------------------------------------------------
# Generate Session Token
# --------------------------------------------------

def generate_session_token(user_id, role):
    """Generate a temporary session token."""

    token = secrets.token_hex(32)

    return {
        "session_token": token,
        "user_id": user_id,
        "role": role
    }


# --------------------------------------------------
# Login
# --------------------------------------------------

def login_user(email, password):
    """Authenticate a user with their email and password."""

    account = find_account(email or "")

    if account is not None:

        user_id, name, stored_email, stored_hash, role = account

        if secrets.compare_digest(hash_password(password), stored_hash):

            session = generate_session_token(user_id, role)
            session["name"] = name
            session["dashboard"] = route_to_role_dashboard(role)

            return {
                "success": True,
                "message": "Login successful.",
                "session": session
            }

    return {
        "success": False,
        "message": "Invalid email or password.",
        "session": None
    }
