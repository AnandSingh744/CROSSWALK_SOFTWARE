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

def register_user(name, email, password, role):
    """
    Register a new user account.

    Returns:
        Success message or error message.
    """

    # Check required fields
    if not name or not email or not password or not role:
        return "Please complete all required fields."

    # Check duplicate account
    if find_account(email) is not None:
        return "An account with this email already exists."

    # Generate unique user ID
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT User_Id FROM users ORDER BY User_Id DESC LIMIT 1"
        )

        last_user = cursor.fetchone()

        if last_user:
            last_number = int(last_user[0].replace("USR", ""))
            user_id = f"USR{last_number + 1:03d}"
        else:
            user_id = "USR001"

        # Hash password
        password_hash = hash_password(password)

        # Store account
        cursor.execute(
            """
            INSERT INTO users
            (User_Id, Name, Email, Password_Hash, Role)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                name.strip(),
                email.strip(),
                password_hash,
                role
            )
        )

        conn.commit()

        return "Registration successful."

    except Exception as e:
        conn.rollback()
        return f"Registration failed: {e}"

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
    """
    Authenticate a user.

    Maximum attempts = 3.
    """

    attempts = 0
    max_attempts = 3

    while attempts < max_attempts:

        account = find_account(email)

        if account is not None:

            user_id, name, stored_email, stored_hash, role = account

            entered_hash = hash_password(password)

            if entered_hash == stored_hash:

                dashboard = route_to_role_dashboard(role)

                session = generate_session_token(
                    user_id,
                    role
                )

                session["name"] = name
                session["dashboard"] = dashboard

                return {
                    "success": True,
                    "message": "Login successful.",
                    "session": session
                }

        attempts += 1

    return {
        "success": False,
        "message": "Invalid email or password.",
        "session": None
    }