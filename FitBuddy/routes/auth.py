from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
import secrets
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from database.models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


def ensure_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)


def validate_csrf(token):
    return bool(token) and secrets.compare_digest(
        token, session.get("csrf_token", "")
    )


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "info")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    ensure_csrf_token()

    if request.method == "POST":
        if not validate_csrf(request.form.get("csrf_token")):
            flash("Your form session expired. Please try again.", "error")
            return render_template("register.html", page_title="Create account")

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = []
        if not 2 <= len(name) <= 100:
            errors.append("Name must be between 2 and 100 characters.")
        if "@" not in email or len(email) > 255:
            errors.append("Enter a valid email address.")
        if len(password) < 8:
            errors.append("Password must contain at least 8 characters.")
        if password != confirm_password:
            errors.append("Passwords do not match.")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("register.html", page_title="Create account")

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash("An account with that email already exists.", "error")
            return render_template("register.html", page_title="Create account")

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("That email is already registered.", "error")
            return render_template("register.html", page_title="Create account")

        session.clear()
        session["user_id"] = user.id
        ensure_csrf_token()
        flash("Welcome to FitBuddy. Let's build your profile.", "success")
        return redirect(url_for("fitness.profile"))

    return render_template("register.html", page_title="Create account")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    ensure_csrf_token()

    if request.method == "POST":
        if not validate_csrf(request.form.get("csrf_token")):
            flash("Your form session expired. Please try again.", "error")
            return render_template("login.html", page_title="Log in")

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            flash("Email or password is incorrect.", "error")
            return render_template("login.html", page_title="Log in")

        session.clear()
        session["user_id"] = user.id
        ensure_csrf_token()
        flash("Welcome back.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("login.html", page_title="Log in")


@auth_bp.post("/logout")
def logout():
    if not validate_csrf(request.form.get("csrf_token")):
        flash("Your session expired. Please try again.", "error")
        return redirect(url_for("main.index"))

    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("main.index"))
