"""
routes.py - Flask API Routes
Database Manager: Prabhat Maharjan (0371462)
Group 13 - Indoor Plant Recommendation System

All routes call db_utils functions.
Bishesh (Backend Developer) wires these into the frontend.

Endpoints:
  POST /api/register
  POST /api/login
  POST /api/guest
  POST /api/preferences
  POST /api/environment
  POST /api/interact
  POST /api/rate
  POST /api/review
  POST /api/recommend
  GET  /api/recommendations
  GET  /api/plants
  GET  /api/plants/<plant_id>
"""

from flask import Blueprint, request, jsonify, session
from app import db_utils

main = Blueprint("main", __name__)


# ── Helper: get user/guest from session ─────────────────
def get_session_identity():
    return session.get("user_id"), session.get("guest_id")


# ════════════════════════════════════════════════
# AUTH ROUTES
# ════════════════════════════════════════════════

@main.route("/api/register", methods=["POST"])
def register():
    """Register a new user."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    required = ["name", "email", "password", "experience_level"]
    for field in required:
        if field not in data or not str(data[field]).strip():
            return jsonify({"success": False, "error": f"Missing field: {field}"}), 400

    result = db_utils.register_user(
        name=data["name"],
        email=data["email"],
        password=data["password"],
        experience_level=data["experience_level"]
    )

    if result["success"]:
        session["user_id"] = result["user_id"]
        session.pop("guest_id", None)
        return jsonify(result), 201
    return jsonify(result), 409


@main.route("/api/login", methods=["POST"])
def login():
    """Login an existing user."""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    if "email" not in data or "password" not in data:
        return jsonify({"success": False, "error": "email and password required"}), 400

    result = db_utils.login_user(data["email"], data["password"])

    if result["success"]:
        session["user_id"] = result["user"]["user_id"]
        session.pop("guest_id", None)
        return jsonify(result), 200
    return jsonify(result), 401


@main.route("/api/logout", methods=["POST"])
def logout():
    """Clear the session."""
    session.clear()
    return jsonify({"success": True, "message": "Logged out"}), 200


@main.route("/api/guest", methods=["POST"])
def guest_session():
    """Create a guest session."""
    result = db_utils.create_guest_session()
    if result["success"]:
        session["guest_id"] = result["guest_id"]
        session.pop("user_id", None)
        return jsonify(result), 201
    return jsonify(result), 500


# ════════════════════════════════════════════════
# PREFERENCES & ENVIRONMENT ROUTES
# ════════════════════════════════════════════════

@main.route("/api/preferences", methods=["POST"])
def save_preferences():
    """Save user preferences (registered users only)."""
    user_id, _ = get_session_identity()
    if not user_id:
        return jsonify({"success": False, "error": "Login required"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    required = ["preferred_light", "preferred_maintenance", "preferred_size"]
    for field in required:
        if field not in data:
            return jsonify({"success": False, "error": f"Missing field: {field}"}), 400

    result = db_utils.save_user_preference(
        user_id=user_id,
        preferred_light=data["preferred_light"],
        preferred_maintenance=data["preferred_maintenance"],
        preferred_size=data["preferred_size"],
        pet_friendly_required=data.get("pet_friendly_required", False)
    )

    status = 200 if result["success"] else 400
    return jsonify(result), status


@main.route("/api/environment", methods=["POST"])
def save_environment():
    """Save user environment data (registered users only)."""
    user_id, _ = get_session_identity()
    if not user_id:
        return jsonify({"success": False, "error": "Login required"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400

    required = ["light_level", "humidity", "temperature", "room_size"]
    for field in required:
        if field not in data:
            return jsonify({"success": False, "error": f"Missing field: {field}"}), 400

    result = db_utils.save_environment(
        user_id=user_id,
        light_level=data["light_level"],
        humidity=data["humidity"],
        temperature=data["temperature"],
        room_size=data["room_size"]
    )

    status = 200 if result["success"] else 400
    return jsonify(result), status


# ════════════════════════════════════════════════
# INTERACTION, RATING, REVIEW ROUTES
# ════════════════════════════════════════════════

@main.route("/api/interact", methods=["POST"])
def interact():
    """Log a plant interaction (user or guest)."""
    user_id, guest_id = get_session_identity()
    if not user_id and not guest_id:
        return jsonify({"success": False, "error": "Session required"}), 401

    data = request.get_json()
    if not data or "plant_id" not in data or "interaction_type" not in data:
        return jsonify({"success": False, "error": "plant_id and interaction_type required"}), 400

    result = db_utils.log_interaction(
        plant_id=int(data["plant_id"]),
        interaction_type=data["interaction_type"],
        user_id=user_id,
        guest_id=guest_id
    )

    status = 201 if result["success"] else 400
    return jsonify(result), status


@main.route("/api/rate", methods=["POST"])
def rate_plant():
    """Rate a plant 1-5 (registered users only)."""
    user_id, _ = get_session_identity()
    if not user_id:
        return jsonify({"success": False, "error": "Login required to rate plants"}), 401

    data = request.get_json()
    if not data or "plant_id" not in data or "rating_value" not in data:
        return jsonify({"success": False, "error": "plant_id and rating_value required"}), 400

    result = db_utils.submit_rating(
        user_id=user_id,
        plant_id=int(data["plant_id"]),
        rating_value=int(data["rating_value"])
    )

    status = 200 if result["success"] else 400
    return jsonify(result), status


@main.route("/api/review", methods=["POST"])
def review_plant():
    """Submit a text review (registered users only)."""
    user_id, _ = get_session_identity()
    if not user_id:
        return jsonify({"success": False, "error": "Login required to write reviews"}), 401

    data = request.get_json()
    if not data or "plant_id" not in data or "review_text" not in data:
        return jsonify({"success": False, "error": "plant_id and review_text required"}), 400

    result = db_utils.submit_review(
        user_id=user_id,
        plant_id=int(data["plant_id"]),
        review_text=data["review_text"]
    )

    status = 201 if result["success"] else 400
    return jsonify(result), status


# ════════════════════════════════════════════════
# RECOMMENDATION ROUTES
# ════════════════════════════════════════════════

@main.route("/api/recommend", methods=["POST"])
def recommend():
    """
    Generate and store recommendations.
    - Registered user → CF (item-item cosine similarity)
    - Guest → CF average rating fallback / interaction count fallback
    """
    user_id, guest_id = get_session_identity()

    if not user_id and not guest_id:
        return jsonify({"success": False, "error": "Session required"}), 401

    if user_id:
        result = db_utils.generate_cf_recommendation(user_id=user_id)
    else:
        result = db_utils.generate_guest_recommendation(guest_id=guest_id)

    status = 200 if result["success"] else 500
    return jsonify(result), status


@main.route("/api/recommendations", methods=["GET"])
def get_recommendations():
    """Retrieve stored recommendations for current session."""
    user_id, guest_id = get_session_identity()

    if not user_id and not guest_id:
        return jsonify({"success": False, "error": "Session required"}), 401

    result = db_utils.get_recommendations(user_id=user_id, guest_id=guest_id)
    return jsonify(result), 200


# ════════════════════════════════════════════════
# PLANT ROUTES
# ════════════════════════════════════════════════

@main.route("/api/plants", methods=["GET"])
def get_plants():
    """Get all plants."""
    result = db_utils.get_all_plants()
    return jsonify(result), 200


@main.route("/api/plants/<int:plant_id>", methods=["GET"])
def get_plant(plant_id):
    """Get a single plant by ID."""
    result = db_utils.get_plant_by_id(plant_id)
    status = 200 if result["success"] else 404
    return jsonify(result), status
