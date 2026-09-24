import json
import secrets
from datetime import datetime, timezone

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from database import db
from database.models import FitnessPlan, FitnessProfile, User
from routes.auth import ensure_csrf_token, login_required, validate_csrf
from services.gemini_service import GeminiServiceError, generate_fitness_plan

fitness_bp = Blueprint("fitness", __name__)



def current_user():
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


def parse_profile_form(form):
    errors = []

    def text(name, label, max_length=500, required=True):
        value = form.get(name, "").strip()
        if required and not value:
            errors.append(f"{label} is required.")
        if len(value) > max_length:
            errors.append(f"{label} is too long.")
        return value

    def integer(name, label, minimum, maximum):
        raw = form.get(name, "").strip()
        try:
            value = int(raw)
        except ValueError:
            errors.append(f"{label} must be a whole number.")
            return None
        if not minimum <= value <= maximum:
            errors.append(f"{label} must be between {minimum} and {maximum}.")
        return value

    def decimal(name, label, minimum, maximum):
        raw = form.get(name, "").strip()
        try:
            value = float(raw)
        except ValueError:
            errors.append(f"{label} must be a number.")
            return None
        if not minimum <= value <= maximum:
            errors.append(f"{label} must be between {minimum} and {maximum}.")
        return value

    allowed = {
        "gender": {"female", "male", "non-binary", "prefer-not-to-say"},
        "fitness_level": {"beginner", "intermediate", "advanced"},
        "primary_goal": {
            "general fitness",
            "strength",
            "muscle building",
            "fat loss",
            "endurance",
            "mobility",
        },
        "activity_level": {"sedentary", "lightly active", "moderately active", "very active"},
        "workout_location": {"home", "gym", "outdoors", "mixed"},
        "diet_preference": {
            "no preference",
            "vegetarian",
            "vegan",
            "pescatarian",
            "eggetarian",
        },
    }

    data = {
        "name": text("name", "Name", 100),
        "age": integer("age", "Age", 13, 100),
        "gender": text("gender", "Gender", 40),
        "height_cm": decimal("height_cm", "Height", 100, 250),
        "weight_kg": decimal("weight_kg", "Weight", 25, 350),
        "fitness_level": text("fitness_level", "Fitness level", 40),
        "primary_goal": text("primary_goal", "Primary goal", 80),
        "activity_level": text("activity_level", "Activity level", 60),
        "workout_days": integer("workout_days", "Workout days", 1, 7),
        "session_duration": integer("session_duration", "Session duration", 15, 180),
        "workout_location": text("workout_location", "Workout location", 80),
        "equipment": text("equipment", "Available equipment", 500, required=False),
        "diet_preference": text("diet_preference", "Diet preference", 80),
        "additional_notes": text("additional_notes", "Additional notes", 1500, required=False),
    }

    for field, choices in allowed.items():
        if data[field] and data[field] not in choices:
            errors.append(f"Invalid value submitted for {field.replace('_', ' ')}.")

    return data, errors


@fitness_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    ensure_csrf_token()
    user = current_user()
    profile = user.fitness_profile

    if request.method == "POST":
        if not validate_csrf(request.form.get("csrf_token")):
            flash("Your form session expired. Please try again.", "error")
            return render_template("profile.html", page_title="Your profile", profile=profile)

        data, errors = parse_profile_form(request.form)

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("profile.html", page_title="Your profile", profile=profile)

        if not profile:
            profile = FitnessProfile(user_id=user.id, **data)
            db.session.add(profile)
        else:
            for key, value in data.items():
                setattr(profile, key, value)

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            current_app.logger.exception("Profile save failed.")
            flash("We could not save your profile. Please try again.", "error")
            return render_template("profile.html", page_title="Your profile", profile=profile)

        flash("Your fitness profile has been saved.", "success")
        return redirect(url_for("fitness.profile"))

    return render_template("profile.html", page_title="Your profile", profile=profile)


@fitness_bp.route("/plan/new", methods=["GET", "POST"])
@login_required
def create_plan():
    ensure_csrf_token()
    user = current_user()
    profile = user.fitness_profile

    if request.method == "GET":
        if not profile:
            flash("Complete your fitness profile before generating a plan.", "info")
            return redirect(url_for("fitness.profile"))
        return render_template("create_plan.html", page_title="Create a plan", profile=profile)

    if not validate_csrf(request.form.get("csrf_token")):
        flash("Your form session expired. Please try again.", "error")
        return redirect(url_for("fitness.create_plan"))

    if not profile:
        flash("Complete your fitness profile before generating a plan.", "info")
        return redirect(url_for("fitness.profile"))

    service_profile = {
        "name": profile.name,
        "age": profile.age,
        "gender": profile.gender,
        "height_cm": profile.height_cm,
        "weight_kg": profile.weight_kg,
        "fitness_level": profile.fitness_level,
        "primary_goal": profile.primary_goal,
        "activity_level": profile.activity_level,
        "workout_days": profile.workout_days,
        "session_duration": profile.session_duration,
        "workout_location": profile.workout_location,
        "equipment": profile.equipment,
        "diet_preference": profile.diet_preference,
        "additional_notes": profile.additional_notes,
        "gemini_api_key": current_app.config.get("GEMINI_API_KEY"),
        "gemini_model": current_app.config.get("GEMINI_MODEL"),
        "gemini_timeout_ms": current_app.config.get("GEMINI_TIMEOUT_MS"),
    }

    try:
        plan_data = generate_fitness_plan(service_profile)
    except GeminiServiceError as exc:
        flash(str(exc), "error")
        return redirect(url_for("fitness.create_plan"))
    except Exception:
        current_app.logger.exception("Unexpected plan generation error.")
        flash("We could not generate your plan right now. Please try again.", "error")
        return redirect(url_for("fitness.create_plan"))

    plan = FitnessPlan(
        user_id=user.id,
        title=plan_data["plan_title"][:180],
        goal=profile.primary_goal,
        duration=plan_data["duration"][:80],
        plan_json=json.dumps(plan_data, ensure_ascii=False),
    )
    db.session.add(plan)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Plan save failed.")
        flash("The plan was generated but could not be saved. Please try again.", "error")
        return redirect(url_for("fitness.create_plan"))

    flash("Your personalized plan is ready.", "success")
    return redirect(url_for("fitness.view_plan", plan_id=plan.id))


@fitness_bp.get("/plan/<int:plan_id>")
@login_required
def view_plan(plan_id):
    plan = FitnessPlan.query.filter_by(
        id=plan_id,
        user_id=session["user_id"],
    ).first_or_404()

    try:
        plan_data = json.loads(plan.plan_json)
    except json.JSONDecodeError:
        flash("This saved plan could not be read.", "error")
        return redirect(url_for("fitness.history"))

    return render_template(
        "plan.html",
        page_title=plan.title,
        plan=plan,
        plan_data=plan_data,
    )


@fitness_bp.get("/history")
@login_required
def history():
    plans = (
        FitnessPlan.query.filter_by(user_id=session["user_id"])
        .order_by(FitnessPlan.created_at.desc())
        .all()
    )
    return render_template("history.html", page_title="Plan history", plans=plans)
