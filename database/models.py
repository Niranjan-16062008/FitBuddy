from datetime import datetime, timezone

from database import db


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    fitness_profile = db.relationship(
        "FitnessProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    plans = db.relationship(
        "FitnessPlan",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="desc(FitnessPlan.created_at)",
    )
    progress_entries = db.relationship(
        "Progress",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class FitnessProfile(db.Model):
    __tablename__ = "fitness_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False
    )

    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(40), nullable=False)
    height_cm = db.Column(db.Float, nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)
    fitness_level = db.Column(db.String(40), nullable=False)
    primary_goal = db.Column(db.String(80), nullable=False)
    activity_level = db.Column(db.String(60), nullable=False)
    workout_days = db.Column(db.Integer, nullable=False)
    session_duration = db.Column(db.Integer, nullable=False)
    workout_location = db.Column(db.String(80), nullable=False)
    equipment = db.Column(db.String(500), nullable=False, default="")
    diet_preference = db.Column(db.String(80), nullable=False)
    additional_notes = db.Column(db.Text, nullable=True, default="")
    updated_at = db.Column(db.DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user = db.relationship("User", back_populates="fitness_profile")


class FitnessPlan(db.Model):
    __tablename__ = "fitness_plans"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(180), nullable=False)
    goal = db.Column(db.String(80), nullable=False)
    duration = db.Column(db.String(80), nullable=False)
    plan_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

    user = db.relationship("User", back_populates="plans")
    progress_entries = db.relationship(
        "Progress",
        back_populates="plan",
        cascade="all, delete-orphan",
    )


class Progress(db.Model):
    __tablename__ = "progress"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey("fitness_plans.id"), nullable=True)
    workout_date = db.Column(db.Date, nullable=False)
    workout_name = db.Column(db.String(180), nullable=False)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    notes = db.Column(db.String(500), nullable=True, default="")

    user = db.relationship("User", back_populates="progress_entries")
    plan = db.relationship("FitnessPlan", back_populates="progress_entries")
