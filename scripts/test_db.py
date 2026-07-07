"""
test_db.py - Database Testing Script
    python scripts/test_db.py
"""

import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app import db_utils
from app.models import db, Plant, User, Rating

app = create_app()

PASS = "✅ PASS"
FAIL = "❌ FAIL"


def run_tests():
    with app.app_context():
        print("\n🧪 Running Database Tests")
        print("=" * 50)

        # ── Test 1: Plant count ───────────────────────────
        plant_count = Plant.query.count()
        status = PASS if plant_count > 0 else FAIL
        print(f"{status}  Plants in database: {plant_count}")

        # ── Test 2: Register user ─────────────────────────
        result = db_utils.register_user(
            name="Test User",
            email="testuser_unique998@example.com",
            password="TestPass123",
            experience_level="Beginner"
        )
        status = PASS if result["success"] else FAIL
        print(f"{status}  register_user(): {result}")
        user_id = result.get("user_id")

        # ── Test 3: Duplicate registration ────────────────
        result2 = db_utils.register_user(
            name="Test User",
            email="testuser_unique999@example.com",
            password="TestPass123",
            experience_level="Beginner"
        )
        status = PASS if not result2["success"] else FAIL
        print(f"{status}  Duplicate email blocked: {result2.get('error')}")

        # ── Test 4: Login ─────────────────────────────────
        login_result = db_utils.login_user("testuser_unique999@example.com", "TestPass123")
        status = PASS if login_result["success"] else FAIL
        print(f"{status}  login_user(): success={login_result['success']}")

        # ── Test 5: Wrong password ────────────────────────
        bad_login = db_utils.login_user("testuser_unique999@example.com", "WrongPassword")
        status = PASS if not bad_login["success"] else FAIL
        print(f"{status}  Wrong password blocked: {bad_login.get('error')}")

        # ── Test 6: Guest session ─────────────────────────
        guest_result = db_utils.create_guest_session()
        status = PASS if guest_result["success"] else FAIL
        print(f"{status}  create_guest_session(): guest_id={guest_result.get('guest_id')}")
        guest_id = guest_result.get("guest_id")

        if user_id:
            # ── Test 7: Save preferences ──────────────────
            pref_result = db_utils.save_user_preference(
                user_id=user_id,
                preferred_light="Medium",
                preferred_maintenance="Low",
                preferred_size="Small",
                pet_friendly_required=True
            )
            status = PASS if pref_result["success"] else FAIL
            print(f"{status}  save_user_preference(): {pref_result}")

            # ── Test 8: Save environment ──────────────────
            env_result = db_utils.save_environment(
                user_id=user_id,
                light_level="Medium",
                humidity="Low",
                temperature="Moderate",
                room_size="Small"
            )
            status = PASS if env_result["success"] else FAIL
            print(f"{status}  save_environment(): {env_result}")

            # ── Test 9: Log interaction ───────────────────
            first_plant = Plant.query.first()
            if first_plant:
                inter_result = db_utils.log_interaction(
                    plant_id=first_plant.plant_id,
                    interaction_type="View",
                    user_id=user_id
                )
                status = PASS if inter_result["success"] else FAIL
                print(f"{status}  log_interaction() (user): {inter_result}")

                # ── Test 10: Submit rating ─────────────────
                rate_result = db_utils.submit_rating(
                    user_id=user_id,
                    plant_id=first_plant.plant_id,
                    rating_value=4
                )
                status = PASS if rate_result["success"] else FAIL
                print(f"{status}  submit_rating(): {rate_result}")

                # ── Test 11: Submit review ─────────────────
                review_result = db_utils.submit_review(
                    user_id=user_id,
                    plant_id=first_plant.plant_id,
                    review_text="Great plant, very easy to care for!"
                )
                status = PASS if review_result["success"] else FAIL
                print(f"{status}  submit_review(): {review_result}")

                # ── Test 12: Invalid rating value ──────────
                bad_rate = db_utils.submit_rating(user_id=user_id,
                                                   plant_id=first_plant.plant_id,
                                                   rating_value=10)
                status = PASS if not bad_rate["success"] else FAIL
                print(f"{status}  Invalid rating blocked: {bad_rate.get('error')}")

            # ── Test 13: CF Recommendation ────────────────
            # Add a few more ratings to get CF working
            plants = Plant.query.limit(5).all()
            for i, p in enumerate(plants):
                db_utils.submit_rating(user_id=user_id, plant_id=p.plant_id,
                                        rating_value=(i % 5) + 1)

            cf_result = db_utils.generate_cf_recommendation(user_id=user_id)
            status = PASS if cf_result["success"] else FAIL
            rec_count = len(cf_result.get("recommendations", []))
            print(f"{status}  generate_cf_recommendation(): {rec_count} recommendations, algo={cf_result.get('algorithm')}")

        # ── Test 14: Guest recommendation ────────────────
        if guest_id:
            if first_plant:
                db_utils.log_interaction(plant_id=first_plant.plant_id,
                                          interaction_type="View", guest_id=guest_id)
            guest_rec = db_utils.generate_guest_recommendation(guest_id=guest_id)
            status = PASS if guest_rec["success"] else FAIL
            rec_count = len(guest_rec.get("recommendations", []))
            print(f"{status}  generate_guest_recommendation(): {rec_count} recs, algo={guest_rec.get('algorithm')}")

        # ── Test 15: Get all plants ───────────────────────
        all_plants = db_utils.get_all_plants()
        status = PASS if all_plants["success"] and len(all_plants["plants"]) > 0 else FAIL
        print(f"{status}  get_all_plants(): {len(all_plants['plants'])} plants returned")

        # ── Test 16: Get plant by ID ──────────────────────
        first_plant = Plant.query.first()
        if first_plant:
            plant_detail = db_utils.get_plant_by_id(first_plant.plant_id)
            status = PASS if plant_detail["success"] else FAIL
            print(f"{status}  get_plant_by_id({first_plant.plant_id}): {plant_detail['plant']['plant_name']}")

        print("\n" + "=" * 50)
        print("🏁 Tests complete.\n")


if __name__ == "__main__":
    run_tests()
