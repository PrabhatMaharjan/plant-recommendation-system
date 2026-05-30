"""
__init__.py - Flask App Factory
"""

import os
from flask import Flask
from app.models import db


def create_app():
    app = Flask(__name__)

    # SQLite database path
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DB_PATH = os.path.join(BASE_DIR, "..", "plant_recommendation.db")

    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")

    # Init SQLAlchemy
    db.init_app(app)

    # Enable foreign key enforcement for SQLite
    from sqlalchemy import event
    from sqlalchemy.engine import Engine
    import sqlite3

    @event.listens_for(Engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        if isinstance(dbapi_connection, sqlite3.Connection):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    # Register Blueprints
    from app.routes import main
    app.register_blueprint(main)

    # Create tables if they don't exist
    with app.app_context():
        db.create_all()
        _create_indexes(db)

    return app


def _create_indexes(db):
    from sqlalchemy import text
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_plant_light ON Plant(light_requirement)",
        "CREATE INDEX IF NOT EXISTS idx_plant_maintenance ON Plant(maintenance_level)",
        "CREATE INDEX IF NOT EXISTS idx_rating_user ON Rating(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_rating_plant ON Rating(plant_id)",
        "CREATE INDEX IF NOT EXISTS idx_interaction_user ON Interaction(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_interaction_guest ON Interaction(guest_id)",
        "CREATE INDEX IF NOT EXISTS idx_recommendation_user ON Recommendation(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_recommendation_guest ON Recommendation(guest_id)",
    ]
    for sql in indexes:
        try:
            db.session.execute(text(sql))
        except Exception:
            pass
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
