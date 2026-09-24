import json
import re

from google import genai
from google.genai import types


class GeminiServiceError(Exception):
    """Safe, user-facing Gemini service failure."""


REQUIRED_TOP_LEVEL_KEYS = {
    "plan_title",
    "summary",
    "duration",
    "weekly_schedule",
    "nutrition_guidance",
    "meal_suggestions",
    "tips",
    "safety_note",
}


def _clean_json_text(text):
    if not text:
        raise GeminiServiceError("Gemini returned an empty response.")

    cleaned = text.strip()
    cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def _validate_plan(plan):
    if not isinstance(plan, dict):
        raise GeminiServiceError("The AI response was not a JSON object.")

    missing = REQUIRED_TOP_LEVEL_KEYS - set(plan.keys())
    if missing:
        raise GeminiServiceError(
            "The AI response was missing required planning sections."
        )

    if not isinstance(plan["weekly_schedule"], list) or not plan["weekly_schedule"]:
        raise GeminiServiceError("The AI response did not contain a weekly schedule.")

    if not isinstance(plan["nutrition_guidance"], list):
        raise GeminiServiceError("The AI nutrition section was invalid.")

    if not isinstance(plan["meal_suggestions"], list):
        raise GeminiServiceError("The AI meal suggestions were invalid.")

    if not isinstance(plan["tips"], list):
        raise GeminiServiceError("The AI tips section was invalid.")

    for day in plan["weekly_schedule"]:
        if not isinstance(day, dict):
            raise GeminiServiceError("A weekly schedule entry was invalid.")
        for key in ("day", "focus", "workouts"):
            if key not in day:
                raise GeminiServiceError("A weekly schedule entry is incomplete.")
        if not isinstance(day["workouts"], list):
            raise GeminiServiceError("A workout list was invalid.")

        for workout in day["workouts"]:
            if not isinstance(workout, dict):
                raise GeminiServiceError("A workout entry was invalid.")
            for key in ("name", "exercises"):
                if key not in workout:
                    raise GeminiServiceError("A workout entry is incomplete.")
            if not isinstance(workout["exercises"], list):
                raise GeminiServiceError("An exercise list was invalid.")

            for exercise in workout["exercises"]:
                if not isinstance(exercise, dict):
                    raise GeminiServiceError("An exercise entry was invalid.")
                for key in ("name", "sets", "repetitions", "rest", "notes"):
                    if key not in exercise:
                        raise GeminiServiceError("An exercise entry is incomplete.")

    return plan


def generate_fitness_plan(profile):
    api_key = profile.get("gemini_api_key")
    model_name = profile.get("gemini_model", "gemini-3.8-flash")
    timeout_ms = profile.get("gemini_timeout_ms", 90000)

    if not api_key:
        raise GeminiServiceError(
            "The Gemini API key is not configured. Add GEMINI_API_KEY to your .env file."
        )

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=timeout_ms),
    )

    profile_text = f"""
Name: {profile['name']}
Age: {profile['age']}
Gender: {profile['gender']}
Height: {profile['height_cm']} cm
Weight: {profile['weight_kg']} kg
Fitness level: {profile['fitness_level']}
Primary goal: {profile['primary_goal']}
Activity level: {profile['activity_level']}
Workout days per week: {profile['workout_days']}
Session duration: {profile['session_duration']} minutes
Workout location: {profile['workout_location']}
Available equipment: {profile['equipment'] or 'None specified'}
Diet preference: {profile['diet_preference']}
Additional notes: {profile['additional_notes'] or 'None'}
""".strip()

    schema = {
        "type": "OBJECT",
        "properties": {
            "plan_title": {"type": "STRING"},
            "summary": {"type": "STRING"},
            "duration": {"type": "STRING"},
            "weekly_schedule": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "day": {"type": "STRING"},
                        "focus": {"type": "STRING"},
                        "workouts": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "name": {"type": "STRING"},
                                    "warmup": {
                                        "type": "ARRAY",
                                        "items": {"type": "STRING"},
                                    },
                                    "exercises": {
                                        "type": "ARRAY",
                                        "items": {
                                            "type": "OBJECT",
                                            "properties": {
                                                "name": {"type": "STRING"},
                                                "sets": {"type": "STRING"},
                                                "repetitions": {"type": "STRING"},
                                                "rest": {"type": "STRING"},
                                                "notes": {"type": "STRING"},
                                            },
                                            "required": [
                                                "name",
                                                "sets",
                                                "repetitions",
                                                "rest",
                                                "notes",
                                            ],
                                        },
                                    },
                                    "cooldown": {
                                        "type": "ARRAY",
                                        "items": {"type": "STRING"},
                                    },
                                },
                                "required": ["name", "warmup", "exercises", "cooldown"],
                            },
                        },
                    },
                    "required": ["day", "focus", "workouts"],
                },
            },
            "nutrition_guidance": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
            },
            "meal_suggestions": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
            },
            "tips": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
            },
            "safety_note": {"type": "STRING"},
        },
        "required": [
            "plan_title",
            "summary",
            "duration",
            "weekly_schedule",
            "nutrition_guidance",
            "meal_suggestions",
            "tips",
            "safety_note",
        ],
    }

    system_instruction = """
You are FitBuddy, a careful fitness-planning assistant. Create practical,
beginner-friendly or appropriately challenging general fitness guidance from
the supplied profile.

Return JSON only and follow the supplied schema exactly.

Important:
- Do not diagnose medical conditions.
- Do not promise specific weight-loss, muscle-gain, or performance results.
- Do not prescribe treatment, medication, supplements, or extreme diets.
- Keep exercise recommendations appropriate to the stated fitness level,
  equipment, location, days per week, and session duration.
- Include sensible warmups, cooldowns, rest, and recovery.
- If the profile contains a medical concern, injury, or unclear safety issue,
  make the safety_note recommend consulting a qualified professional rather
  than attempting to diagnose or treat it.
- Nutrition guidance should be general informational guidance, not medical
  nutrition therapy.
- Use plain, concise language.
""".strip()

    prompt = f"""
Create a personalized fitness plan from this profile:

{profile_text}

The plan must fit the requested number of workout days and session duration.
Use rest/recovery days where appropriate. Make every exercise entry include
sets, repetitions, rest, and a short note.
""".strip()

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=schema,
                temperature=0.35,
                max_output_tokens=7000,
            ),
        )
    except Exception as exc:
        message = str(exc).lower()
        if "timeout" in message or "timed out" in message:
            raise GeminiServiceError(
                "Gemini took too long to respond. Please try generating the plan again."
            ) from exc
        if "api key" in message or "permission" in message or "unauthenticated" in message:
            raise GeminiServiceError(
                "Gemini could not authenticate the request. Check GEMINI_API_KEY in .env."
            ) from exc
        if "429" in message or "resource exhausted" in message:
            raise GeminiServiceError(
                "Gemini is temporarily busy. Please wait a moment and try again."
            ) from exc
        raise GeminiServiceError(
            "Gemini could not generate the plan right now. Please try again."
        ) from exc

    try:
        raw_text = response.text
        plan = json.loads(_clean_json_text(raw_text))
        return _validate_plan(plan)
    except GeminiServiceError:
        raise
    except (TypeError, json.JSONDecodeError, ValueError) as exc:
        raise GeminiServiceError(
            "Gemini returned a response that could not be safely converted into a fitness plan."
        ) from exc
