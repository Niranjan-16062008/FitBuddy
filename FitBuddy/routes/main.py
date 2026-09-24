from flask import Blueprint, redirect, render_template, url_for

from datetime import datetime, timezone

from database.models import FitnessPlan
from database import db


main_bp = Blueprint("main", __name__)


@main_bp.get("/")
def index():
    return render_template("index.html", page_title="FitBuddy")


@main_bp.get("/dashboard")
def dashboard():
    if "user_id" not in __import__("flask").session:
        return redirect(url_for("auth.login"))

    user_id = __import__("flask").session["user_id"]
    from database.models import User

    user = db.session.get(User, user_id)
    if not user:
        return redirect(url_for("auth.logout"))

    plans = (
        FitnessPlan.query.filter_by(user_id=user.id)
        .order_by(FitnessPlan.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "dashboard.html",
        page_title="Dashboard",
        user=user,
        plans=plans,
        current_year=datetime.now(timezone.utc).year,
    )
