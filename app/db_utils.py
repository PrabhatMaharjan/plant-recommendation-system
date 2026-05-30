"""
db_utils.py - All Database Operations
Contains:
  - register_user()
  - login_user()
  - create_guest_session()
  - save_user_preference()
  - save_environment()
  - log_interaction()
  - submit_rating()
  - submit_review()
  - generate_cf_recommendation()      <- for registered users
  - generate_guest_recommendation()   <- for guests (CF fallback)
  - get_recommendations()
  - get_all_plants()
"""

import uuid
import bcrypt
import numpy as np
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app.models import (db, User, Guest, UserPreference, Environment,
                         Plant, PlantCategory, Interaction, Rating,
                         Review, Recommendation)


# SECTION 1 — USER MANAGEMENT

def register_user(name: str, email: str, password: str, experience_level: str) -> dict:
    """
    Registers a new user.
    Returns {"success": True, "user_id": int} or {"success": False, "error": str}
    """
    # Validate experience_level
    valid_levels = {"Beginner", "Intermediate", "Expert"}
    if experience_level not in valid_levels:
        return {"success": False, "error": "experience_level must be Beginner, Intermediate, or Expert"}

    # Check email uniqueness
    existing = User.query.filter_by(email=email.strip().lower()).first()
    if existing:
        return {"success": False, "error": "Email already registered"}

    # Hash password with bcrypt
    hashed_pw = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    new_user = User(
        name=name.strip(),
        email=email.strip().lower(),
        password=hashed_pw,
        experience_level=experience_level
    )
    try:
        db.session.add(new_user)
        db.session.commit()
        return {"success": True, "user_id": new_user.user_id, "name": new_user.name}
    except IntegrityError:
        db.session.rollback()
        return {"success": False, "error": "Database error during registration"}


def login_user(email: str, password: str) -> dict:
    """
    Verifies credentials and returns user data.
    Returns {"success": True, "user": dict} or {"success": False, "error": str}
    """
    user = User.query.filter_by(email=email.strip().lower()).first()
    if not user:
        return {"success": False, "error": "User not found"}

    # Verify bcrypt password
    if not bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
        return {"success": False, "error": "Incorrect password"}

    return {"success": True, "user": user.to_dict()}


def create_guest_session() -> dict:
    """
    Creates a new guest session with a unique UUID.
    Returns {"success": True, "guest_id": int, "session_id": str}
    """
    session_id = str(uuid.uuid4())
    guest = Guest(session_id=session_id)
    try:
        db.session.add(guest)
        db.session.commit()
        return {"success": True, "guest_id": guest.guest_id, "session_id": session_id}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}


# SECTION 2 — USER PREFERENCES & ENVIRONMENT

def save_user_preference(user_id: int, preferred_light: str, preferred_maintenance: str,
                         preferred_size: str, pet_friendly_required: bool) -> dict:
    """
    Saves (or replaces) a user's plant preferences.
    Only one preference record per user — old one is deleted first.
    """
    # Validate user exists
    user = User.query.get(user_id)
    if not user:
        return {"success": False, "error": "Invalid user"}

    # Validate values
    valid_light = {"Low", "Medium", "High"}
    valid_size = {"Small", "Medium", "Large"}
    if preferred_light not in valid_light:
        return {"success": False, "error": "preferred_light must be Low, Medium, or High"}
    if preferred_maintenance not in valid_light:
        return {"success": False, "error": "preferred_maintenance must be Low, Medium, or High"}
    if preferred_size not in valid_size:
        return {"success": False, "error": "preferred_size must be Small, Medium, or Large"}

    # Delete old preference if exists
    UserPreference.query.filter_by(user_id=user_id).delete()

    new_pref = UserPreference(
        user_id=user_id,
        preferred_light=preferred_light,
        preferred_maintenance=preferred_maintenance,
        preferred_size=preferred_size,
        pet_friendly_required=bool(pet_friendly_required)
    )
    try:
        db.session.add(new_pref)
        db.session.commit()
        return {"success": True, "preference_id": new_pref.preference_id}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}


def save_environment(user_id: int, light_level: str, humidity: str,
                     temperature: str, room_size: str) -> dict:
    """
    Saves a user's environment record.
    Multiple environment records allowed (user can have different rooms).
    """
    user = User.query.get(user_id)
    if not user:
        return {"success": False, "error": "Invalid user"}

    valid_light = {"Low", "Medium", "High"}
    valid_temp = {"Cool", "Moderate", "Warm"}
    valid_size = {"Small", "Medium", "Large"}

    if light_level not in valid_light:
        return {"success": False, "error": "light_level must be Low, Medium, or High"}
    if humidity not in valid_light:
        return {"success": False, "error": "humidity must be Low, Medium, or High"}
    if temperature not in valid_temp:
        return {"success": False, "error": "temperature must be Cool, Moderate, or Warm"}
    if room_size not in valid_size:
        return {"success": False, "error": "room_size must be Small, Medium, or Large"}

    env = Environment(
        user_id=user_id,
        light_level=light_level,
        humidity=humidity,
        temperature=temperature,
        room_size=room_size
    )
    try:
        db.session.add(env)
        db.session.commit()
        return {"success": True, "environment_id": env.environment_id}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}


# SECTION 3 — INTERACTIONS, RATINGS, REVIEWS

def log_interaction(plant_id: int, interaction_type: str,
                    user_id: int = None, guest_id: int = None) -> dict:
    """
    Logs a user or guest interaction with a plant.
    interaction_type: View / Click / Save / Share
    Either user_id or guest_id must be provided.
    """
    valid_types = {"View", "Click", "Save", "Share"}
    if interaction_type not in valid_types:
        return {"success": False, "error": "interaction_type must be View, Click, Save, or Share"}

    if user_id is None and guest_id is None:
        return {"success": False, "error": "Either user_id or guest_id must be provided"}

    # Validate plant exists
    plant = Plant.query.get(plant_id)
    if not plant:
        return {"success": False, "error": "Plant not found"}

    interaction = Interaction(
        user_id=user_id,
        guest_id=guest_id,
        plant_id=plant_id,
        interaction_type=interaction_type
    )
    try:
        db.session.add(interaction)
        db.session.commit()
        return {"success": True, "interaction_id": interaction.interaction_id}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}


def submit_rating(user_id: int, plant_id: int, rating_value: int) -> dict:
    """
    Submits or updates a rating (1-5) for a plant by a registered user.
    """
    if not isinstance(rating_value, int) or not (1 <= rating_value <= 5):
        return {"success": False, "error": "rating_value must be an integer between 1 and 5"}

    user = User.query.get(user_id)
    if not user:
        return {"success": False, "error": "Invalid user"}

    plant = Plant.query.get(plant_id)
    if not plant:
        return {"success": False, "error": "Plant not found"}

    # Check if rating already exists → update it
    existing = Rating.query.filter_by(user_id=user_id, plant_id=plant_id).first()
    if existing:
        existing.rating_value = rating_value
        existing.rated_at = datetime.utcnow()
    else:
        new_rating = Rating(user_id=user_id, plant_id=plant_id, rating_value=rating_value)
        db.session.add(new_rating)

    try:
        db.session.commit()
        return {"success": True, "message": "Rating saved"}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}


def submit_review(user_id: int, plant_id: int, review_text: str) -> dict:
    """
    Submits a text review for a plant by a registered user.
    """
    if not review_text or not review_text.strip():
        return {"success": False, "error": "Review text cannot be empty"}

    user = User.query.get(user_id)
    if not user:
        return {"success": False, "error": "Invalid user"}

    plant = Plant.query.get(plant_id)
    if not plant:
        return {"success": False, "error": "Plant not found"}

    review = Review(user_id=user_id, plant_id=plant_id, review_text=review_text.strip())
    try:
        db.session.add(review)
        db.session.commit()
        return {"success": True, "review_id": review.review_id}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}


# SECTION 4 — RECOMMENDATION ENGINE


def generate_cf_recommendation(user_id: int, top_n: int = 10) -> dict:
    """
    Generates recommendations for a REGISTERED USER using Item-Item
    Collaborative Filtering (cosine similarity on rating matrix).

    Steps:
      1. Fetch all ratings from Rating table
      2. Build user-item matrix (pivot)
      3. Get plants already rated by this user
      4. Compute cosine similarity between all plant columns
      5. Predict scores for unrated plants
      6. Rank by predicted score
      7. Clear old recommendations and store new ones in Recommendation table
      8. Return top_n ranked plants with details
    """
    user = User.query.get(user_id)
    if not user:
        return {"success": False, "error": "Invalid user"}

    # Step 1: Fetch all ratings
    all_ratings = Rating.query.all()

    if len(all_ratings) < 2:
        # Not enough data — fall back to most interacted plants
        return _fallback_popular_recommendation(user_id=user_id, top_n=top_n)

    # Step 2: Build user-item matrix as dict {user_id: {plant_id: rating_value}}
    matrix = {}
    for r in all_ratings:
        if r.user_id not in matrix:
            matrix[r.user_id] = {}
        matrix[r.user_id][r.plant_id] = r.rating_value

    # Get all unique plant IDs in rating data
    all_plant_ids = sorted(set(r.plant_id for r in all_ratings))

    if len(all_plant_ids) < 2:
        return _fallback_popular_recommendation(user_id=user_id, top_n=top_n)

    # Step 3: Get plants already rated by this user
    rated_plant_ids = set(matrix.get(user_id, {}).keys())

    # Unrated plants to predict for
    unrated_plant_ids = [pid for pid in all_plant_ids if pid not in rated_plant_ids]

    if not unrated_plant_ids:
        # User rated everything — just return highest rated plants
        return _fallback_popular_recommendation(user_id=user_id, top_n=top_n)

    # Step 4: Build numpy matrix  [users x plants]
    all_user_ids = sorted(matrix.keys())
    user_idx = {uid: i for i, uid in enumerate(all_user_ids)}
    plant_idx = {pid: j for j, pid in enumerate(all_plant_ids)}

    mat = np.zeros((len(all_user_ids), len(all_plant_ids)))
    for uid, ratings_dict in matrix.items():
        for pid, val in ratings_dict.items():
            mat[user_idx[uid]][plant_idx[pid]] = val

    # Step 5: Compute item-item cosine similarity
    # Each column is a plant vector across all users
    plant_mat = mat.T  # shape: [plants x users]
    norms = np.linalg.norm(plant_mat, axis=1, keepdims=True)
    norms[norms == 0] = 1e-10   # avoid division by zero
    plant_mat_norm = plant_mat / norms

    similarity = np.dot(plant_mat_norm, plant_mat_norm.T)  # [plants x plants]

    # Step 6: Predict scores for unrated plants using weighted sum
    target_user_ratings = matrix.get(user_id, {})
    predicted_scores = {}

    for pid in unrated_plant_ids:
        pid_j = plant_idx[pid]
        score = 0.0
        weight_sum = 0.0

        for rated_pid, rated_val in target_user_ratings.items():
            if rated_pid in plant_idx:
                rated_j = plant_idx[rated_pid]
                sim = similarity[pid_j][rated_j]
                score += sim * rated_val
                weight_sum += abs(sim)

        if weight_sum > 0:
            predicted_scores[pid] = score / weight_sum

    # Step 7: Rank plants by predicted score (descending)
    ranked = sorted(predicted_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]

    if not ranked:
        return _fallback_popular_recommendation(user_id=user_id, top_n=top_n)

    # Step 8: Store in Recommendation table (clear old first)
    Recommendation.query.filter_by(user_id=user_id).delete()

    results = []
    for rank, (pid, score) in enumerate(ranked, start=1):
        rec = Recommendation(
            user_id=user_id,
            guest_id=None,
            plant_id=pid,
            algorithm_type="CF",
            recommendation_score=round(float(score), 4),
            rank_position=rank
        )
        db.session.add(rec)

        plant = Plant.query.get(pid)
        if plant:
            results.append({
                "rank": rank,
                "score": round(float(score), 4),
                "plant": plant.to_dict()
            })

    try:
        db.session.commit()
        return {"success": True, "algorithm": "CF", "recommendations": results}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}


def generate_guest_recommendation(guest_id: int, top_n: int = 10) -> dict:
    """
    Generates recommendations for a GUEST using:
    - If enough rating data exists: CF (average rating per plant)
    - Otherwise: cold-start fallback using interaction counts
    - Final fallback: first N plants in database

    Results stored in Recommendation table linked to guest_id.
    """
    guest = Guest.query.get(guest_id)
    if not guest:
        return {"success": False, "error": "Invalid guest session"}

    MINIMUM_RATING_THRESHOLD = 5  # minimum total ratings before CF is used

    all_ratings = Rating.query.all()
    top_plants = []
    algorithm_used = "CBF"

    if len(all_ratings) >= MINIMUM_RATING_THRESHOLD:
        # CF path: rank plants by average rating
        from sqlalchemy import func
        avg_ratings = (
            db.session.query(Rating.plant_id, func.avg(Rating.rating_value).label("avg_score"))
            .group_by(Rating.plant_id)
            .order_by(func.avg(Rating.rating_value).desc())
            .limit(top_n)
            .all()
        )
        top_plants = [(r.plant_id, round(float(r.avg_score), 4)) for r in avg_ratings]
        algorithm_used = "CF"

    if not top_plants:
        # Cold-start: use interaction counts
        from sqlalchemy import func
        interaction_counts = (
            db.session.query(Interaction.plant_id,
                             func.count(Interaction.interaction_id).label("cnt"))
            .group_by(Interaction.plant_id)
            .order_by(func.count(Interaction.interaction_id).desc())
            .limit(top_n)
            .all()
        )
        if interaction_counts:
            max_cnt = interaction_counts[0].cnt if interaction_counts[0].cnt > 0 else 1
            top_plants = [(r.plant_id, round(r.cnt / max_cnt, 4)) for r in interaction_counts]
            algorithm_used = "CBF"

    if not top_plants:
        # Absolute fallback: return first top_n plants with score 0
        plants = Plant.query.limit(top_n).all()
        top_plants = [(p.plant_id, 0.0) for p in plants]
        algorithm_used = "CBF"

    # Clear old guest recommendations and store new ones
    Recommendation.query.filter_by(guest_id=guest_id).delete()

    results = []
    for rank, (pid, score) in enumerate(top_plants, start=1):
        rec = Recommendation(
            user_id=None,
            guest_id=guest_id,
            plant_id=pid,
            algorithm_type=algorithm_used,
            recommendation_score=score,
            rank_position=rank
        )
        db.session.add(rec)

        plant = Plant.query.get(pid)
        if plant:
            results.append({
                "rank": rank,
                "score": score,
                "plant": plant.to_dict()
            })

    try:
        db.session.commit()
        return {"success": True, "algorithm": algorithm_used, "recommendations": results}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}


def _fallback_popular_recommendation(user_id: int = None, top_n: int = 10) -> dict:
    """
    Internal fallback: returns plants ranked by average rating.
    Used when CF cannot run (not enough data).
    """
    from sqlalchemy import func

    avg_ratings = (
        db.session.query(Rating.plant_id, func.avg(Rating.rating_value).label("avg_score"))
        .group_by(Rating.plant_id)
        .order_by(func.avg(Rating.rating_value).desc())
        .limit(top_n)
        .all()
    )

    if not avg_ratings:
        plants = Plant.query.limit(top_n).all()
        avg_ratings = [(p.plant_id, 0.0) for p in plants]
        avg_ratings = [type("obj", (object,), {"plant_id": p, "avg_score": s})()
                       for p, s in avg_ratings]

    if user_id:
        Recommendation.query.filter_by(user_id=user_id).delete()

    results = []
    for rank, r in enumerate(avg_ratings, start=1):
        pid = r.plant_id if hasattr(r, "plant_id") else r[0]
        score = float(r.avg_score) if hasattr(r, "avg_score") else r[1]

        if user_id:
            rec = Recommendation(
                user_id=user_id,
                guest_id=None,
                plant_id=pid,
                algorithm_type="CF",
                recommendation_score=round(score, 4),
                rank_position=rank
            )
            db.session.add(rec)

        plant = Plant.query.get(pid)
        if plant:
            results.append({"rank": rank, "score": round(score, 4), "plant": plant.to_dict()})

    try:
        db.session.commit()
        return {"success": True, "algorithm": "CF_fallback", "recommendations": results}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": str(e)}


# SECTION 5 — RETRIEVAL HELPERS (for Flask routes)

def get_recommendations(user_id: int = None, guest_id: int = None) -> dict:
    """
    Retrieves stored recommendations for a user or guest.
    """
    if user_id:
        recs = (Recommendation.query
                .filter_by(user_id=user_id)
                .order_by(Recommendation.rank_position)
                .all())
    elif guest_id:
        recs = (Recommendation.query
                .filter_by(guest_id=guest_id)
                .order_by(Recommendation.rank_position)
                .all())
    else:
        return {"success": False, "error": "user_id or guest_id required"}

    results = []
    for rec in recs:
        plant = Plant.query.get(rec.plant_id)
        if plant:
            results.append({
                "rank": rec.rank_position,
                "score": rec.recommendation_score,
                "algorithm": rec.algorithm_type,
                "plant": plant.to_dict()
            })

    return {"success": True, "recommendations": results}


def get_all_plants() -> dict:
    """Returns all plants with their category names."""
    plants = Plant.query.all()
    result = []
    for p in plants:
        d = p.to_dict()
        d["category_name"] = p.category.category_name if p.category else None
        result.append(d)
    return {"success": True, "plants": result}


def get_plant_by_id(plant_id: int) -> dict:
    """Returns a single plant by ID."""
    plant = Plant.query.get(plant_id)
    if not plant:
        return {"success": False, "error": "Plant not found"}
    d = plant.to_dict()
    d["category_name"] = plant.category.category_name if plant.category else None
    d["average_rating"] = _get_average_rating(plant_id)
    return {"success": True, "plant": d}


def _get_average_rating(plant_id: int) -> float:
    """Helper to get average rating for a plant."""
    ratings = Rating.query.filter_by(plant_id=plant_id).all()
    if not ratings:
        return 0.0
    return round(sum(r.rating_value for r in ratings) / len(ratings), 2)
