from functools import wraps
from flask import session, redirect, url_for, abort


# -----------------------------
# LOGIN
# -----------------------------

def login_user_session(user_id, role):
    """
    Stores logged-in user's information.
    """

    session.clear()

    session["user_id"] = user_id
    session["role"] = role


# -----------------------------
# LOGOUT
# -----------------------------

def logout_user_session():
    """
    Clears session.
    """

    session.clear()


# -----------------------------
# COMMON CHECK
# -----------------------------

def is_logged_in():
    return session.get("user_id") is not None


# -----------------------------
# ADMIN
# -----------------------------

def admin_required(f):

    @wraps(f)

    def decorated_function(*args, **kwargs):

        if not is_logged_in():
            return redirect(url_for("login"))

        if session.get("role") != "Admin":
            abort(403)

        return f(*args, **kwargs)

    return decorated_function


# -----------------------------
# STAFF
# -----------------------------

def staff_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if not is_logged_in():
            return redirect(url_for("login"))

        if session.get("role") != "Staff":
            abort(403)

        staff_id = kwargs.get("staff_id")

        if staff_id is not None and session.get("user_id") != staff_id:
            abort(403)

        return f(*args, **kwargs)

    return decorated_function


# -----------------------------
# USER
# -----------------------------

def user_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):

        if not is_logged_in():
            return redirect(url_for("login"))

        if session.get("role") != "User":
            abort(403)

        user_id = kwargs.get("user_id")

        if user_id is not None and session.get("user_id") != user_id:
            abort(403)

        return f(*args, **kwargs)

    return decorated_function