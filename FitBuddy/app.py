from pathlib import Path

from flask import Flask, render_template

from config import Config
from database.db import db


BASE_DIR = Path(__file__).resolve().parent


def create_app():
    """Create and configure the FitBuddy Flask application."""

    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "templates"),
        static_folder=str(BASE_DIR / "static"),
    )

    # Load application configuration.
    app.config.from_object(Config)

    # Make sure the required environment variables exist.
    if not app.config.get("SECRET_KEY"):
        raise RuntimeError(
            "SECRET_KEY is missing. Add it to your .env file before "
            "starting FitBuddy."
        )

    if not app.config.get("GEMINI_API_KEY"):
        raise RuntimeError(
            "GEMINI_API_KEY is missing. Add it to your .env file before "
            "starting FitBuddy."
        )

    # Initialize the database.
    db.init_app(app)

    # Import models before creating database tables.
    from database import models  # noqa: F401

    with app.app_context():
        db.create_all()

    # Register application routes.
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.fitness import fitness_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(fitness_bp)

    # Make the current year available to all templates.
    @app.context_processor
    def inject_template_globals():
        from datetime import datetime

        return {
            "current_year": datetime.now().year,
        }

    # Handle missing pages.
    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.html"), 404

    # Handle unexpected server errors without exposing tracebacks.
    @app.errorhandler(500)
    def internal_server_error(error):
        return (
            render_template(
                "404.html",
                error_message="Something went wrong. Please try again.",
            ),
            500,
        )

    return app


app = create_app()


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )