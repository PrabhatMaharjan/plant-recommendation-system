"""
models.py - SQLAlchemy ORM Models
All 10 tables defined here in 3NF with full foreign key constraints.
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# TABLE 1: User

class User(db.Model):
    __tablename__ = "User"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)        # hash
    experience_level = db.Column(db.String(20), nullable=False)  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    preferences = db.relationship("UserPreference", backref="user", lazy=True,
                                  cascade="all, delete-orphan")
    environments = db.relationship("Environment", backref="user", lazy=True,
                                   cascade="all, delete-orphan")
    ratings = db.relationship("Rating", backref="user", lazy=True,
                              cascade="all, delete-orphan")
    reviews = db.relationship("Review", backref="user", lazy=True,
                              cascade="all, delete-orphan")
    interactions = db.relationship("Interaction", backref="user", lazy=True,
                                   cascade="all, delete-orphan",
                                   foreign_keys="Interaction.user_id")
    recommendations = db.relationship("Recommendation", backref="user", lazy=True,
                                      cascade="all, delete-orphan",
                                      foreign_keys="Recommendation.user_id")

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "experience_level": self.experience_level,
            "created_at": self.created_at.isoformat()
        }


# TABLE 2: Guest
class Guest(db.Model):
    __tablename__ = "Guest"

    guest_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session_id = db.Column(db.String(36), nullable=False, unique=True)  # UUID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow,
                              onupdate=datetime.utcnow)

    # Relationships
    interactions = db.relationship("Interaction", backref="guest", lazy=True,
                                   cascade="all, delete-orphan",
                                   foreign_keys="Interaction.guest_id")
    recommendations = db.relationship("Recommendation", backref="guest", lazy=True,
                                      cascade="all, delete-orphan",
                                      foreign_keys="Recommendation.guest_id")

    def to_dict(self):
        return {
            "guest_id": self.guest_id,
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat()
        }


# TABLE 3: UserPreference  (registered users only)
class UserPreference(db.Model):
    __tablename__ = "UserPreference"

    preference_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("User.user_id", ondelete="CASCADE"),
                        nullable=False)
    preferred_light = db.Column(db.String(10), nullable=False)        # Low/Medium/High
    preferred_maintenance = db.Column(db.String(10), nullable=False)  # Low/Medium/High
    preferred_size = db.Column(db.String(10), nullable=False)         # Small/Medium/Large
    pet_friendly_required = db.Column(db.Boolean, nullable=False, default=False)

    def to_dict(self):
        return {
            "preference_id": self.preference_id,
            "user_id": self.user_id,
            "preferred_light": self.preferred_light,
            "preferred_maintenance": self.preferred_maintenance,
            "preferred_size": self.preferred_size,
            "pet_friendly_required": self.pet_friendly_required
        }


# TABLE 4: Environment  (registered users only)
class Environment(db.Model):
    __tablename__ = "Environment"

    environment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("User.user_id", ondelete="CASCADE"),
                        nullable=False)
    light_level = db.Column(db.String(10), nullable=False)    # Low/Medium/High
    humidity = db.Column(db.String(10), nullable=False)       # Low/Medium/High
    temperature = db.Column(db.String(10), nullable=False)    # Cool/Moderate/Warm
    room_size = db.Column(db.String(10), nullable=False)      # Small/Medium/Large
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "environment_id": self.environment_id,
            "user_id": self.user_id,
            "light_level": self.light_level,
            "humidity": self.humidity,
            "temperature": self.temperature,
            "room_size": self.room_size
        }


# TABLE 5: PlantCategory
class PlantCategory(db.Model):
    __tablename__ = "PlantCategory"

    category_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_name = db.Column(db.String(100), nullable=False, unique=True)

    # Relationships
    plants = db.relationship("Plant", backref="category", lazy=True)

    def to_dict(self):
        return {
            "category_id": self.category_id,
            "category_name": self.category_name
        }


# TABLE 6: Plant
class Plant(db.Model):
    __tablename__ = "Plant"

    plant_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plant_name = db.Column(db.String(150), nullable=False, unique=True)
    category_id = db.Column(db.Integer,
                            db.ForeignKey("PlantCategory.category_id", ondelete="RESTRICT"),
                            nullable=False)
    light_requirement = db.Column(db.String(10), nullable=False)    # Low/Medium/High
    watering_frequency = db.Column(db.String(15), nullable=False)   # Daily/Weekly/Bi-weekly
    maintenance_level = db.Column(db.String(10), nullable=False)    # Low/Medium/High
    humidity_requirement = db.Column(db.String(10), nullable=False)  # Low/Medium/High
    temperature_range = db.Column(db.String(10), nullable=False)    # Cool/Moderate/Warm
    toxicity_level = db.Column(db.String(20), nullable=False)       # Non-toxic/Mildly toxic/Toxic
    growth_rate = db.Column(db.String(10), nullable=False)          # Slow/Moderate/Fast
    size_category = db.Column(db.String(10), nullable=False)        # Small/Medium/Large
    image_url = db.Column(db.String(500), nullable=True)            # used for fetching image from usplash

    # Relationships
    ratings = db.relationship("Rating", backref="plant", lazy=True,
                              cascade="all, delete-orphan")
    reviews = db.relationship("Review", backref="plant", lazy=True,
                              cascade="all, delete-orphan")
    interactions = db.relationship("Interaction", backref="plant", lazy=True,
                                   cascade="all, delete-orphan")
    recommendations = db.relationship("Recommendation", backref="plant", lazy=True,
                                      cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "plant_id": self.plant_id,
            "plant_name": self.plant_name,
            "category_id": self.category_id,
            "light_requirement": self.light_requirement,
            "watering_frequency": self.watering_frequency,
            "maintenance_level": self.maintenance_level,
            "humidity_requirement": self.humidity_requirement,
            "temperature_range": self.temperature_range,
            "toxicity_level": self.toxicity_level,
            "growth_rate": self.growth_rate,
            "size_category": self.size_category,
            "image_url": self.image_url
        }


# TABLE 7: Interaction  (both User and Guest)
class Interaction(db.Model):
    __tablename__ = "Interaction"

    interaction_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("User.user_id", ondelete="CASCADE"),
                        nullable=True)   # NULL if guest
    guest_id = db.Column(db.Integer, db.ForeignKey("Guest.guest_id", ondelete="CASCADE"),
                         nullable=True)  # NULL if registered user
    plant_id = db.Column(db.Integer, db.ForeignKey("Plant.plant_id", ondelete="CASCADE"),
                         nullable=False)
    interaction_type = db.Column(db.String(10), nullable=False)  # View/Click/Save/Share
    interaction_time = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "interaction_id": self.interaction_id,
            "user_id": self.user_id,
            "guest_id": self.guest_id,
            "plant_id": self.plant_id,
            "interaction_type": self.interaction_type,
            "interaction_time": self.interaction_time.isoformat()
        }


# TABLE 8: Rating  (registered users only)
class Rating(db.Model):
    __tablename__ = "Rating"

    rating_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("User.user_id", ondelete="CASCADE"),
                        nullable=False)
    plant_id = db.Column(db.Integer, db.ForeignKey("Plant.plant_id", ondelete="CASCADE"),
                         nullable=False)
    rating_value = db.Column(db.Integer, nullable=False)  # 1-5 enforced in db_utils
    rated_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.CheckConstraint("rating_value BETWEEN 1 AND 5", name="check_rating_value"),
        db.UniqueConstraint("user_id", "plant_id", name="unique_user_plant_rating"),
    )

    def to_dict(self):
        return {
            "rating_id": self.rating_id,
            "user_id": self.user_id,
            "plant_id": self.plant_id,
            "rating_value": self.rating_value,
            "rated_at": self.rated_at.isoformat()
        }


# TABLE 9: Review  (registered users only)
class Review(db.Model):
    __tablename__ = "Review"

    review_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("User.user_id", ondelete="CASCADE"),
                        nullable=False)
    plant_id = db.Column(db.Integer, db.ForeignKey("Plant.plant_id", ondelete="CASCADE"),
                         nullable=False)
    review_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "review_id": self.review_id,
            "user_id": self.user_id,
            "plant_id": self.plant_id,
            "review_text": self.review_text,
            "created_at": self.created_at.isoformat()
        }


# TABLE 10: Recommendation  (User or Guest)
class Recommendation(db.Model):
    __tablename__ = "Recommendation"

    recommendation_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("User.user_id", ondelete="CASCADE"),
                        nullable=True)   # NULL if guest
    guest_id = db.Column(db.Integer, db.ForeignKey("Guest.guest_id", ondelete="CASCADE"),
                         nullable=True)  # NULL if registered user
    plant_id = db.Column(db.Integer, db.ForeignKey("Plant.plant_id", ondelete="CASCADE"),
                         nullable=False)
    algorithm_type = db.Column(db.String(10), nullable=False)   # "CF" or "CBF"
    recommendation_score = db.Column(db.Float, nullable=False)
    rank_position = db.Column(db.Integer, nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "recommendation_id": self.recommendation_id,
            "user_id": self.user_id,
            "guest_id": self.guest_id,
            "plant_id": self.plant_id,
            "algorithm_type": self.algorithm_type,
            "recommendation_score": self.recommendation_score,
            "rank_position": self.rank_position,
            "generated_at": self.generated_at.isoformat()
        }
