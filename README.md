# Indoor Plant Recommendation System — Database Layer
### Prabhat Maharjan (0371462) | Group 13 | Database Manager & Optimization

---

## Project Structure

```
plant_recommendation/
├── app/
│   ├── __init__.py          ← Flask app factory (DB config + indexes)
│   ├── models.py            ← All 10 SQLAlchemy table models
│   ├── db_utils.py          ← All database functions (YOUR MAIN WORK)
│   └── routes.py            ← Flask API routes (calls db_utils)
├── scripts/
│   ├── preprocess_plants.py ← Load Kaggle CSVs into SQLite
│   └── test_db.py           ← Test all DB functions
├── data/
│   └── (put your Kaggle CSV files here)
├── run.py                   ← Start Flask server
├── requirements.txt
└── plant_recommendation.db  ← Generated automatically
```

---

## Setup (First Time)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Put Kaggle CSV files in data/ folder
#    If no CSVs found, 60 sample plants are generated automatically

# 3. Load plant data into database
python scripts/preprocess_plants.py

# 4. Run tests to verify everything works
python scripts/test_db.py

# 5. Start the Flask server
python run.py
```

---

## Database Tables (10 total, 3NF)

| Table | Purpose |
|---|---|
| User | Registered user accounts |
| Guest | Anonymous sessions (UUID) |
| UserPreference | Light/size/maintenance preferences |
| Environment | Room conditions (light/humidity/temp/size) |
| PlantCategory | Plant type categories |
| Plant | All plant attributes (60+ records) |
| Interaction | Views, clicks, saves (user or guest) |
| Rating | 1-5 star ratings (registered users only) |
| Review | Text reviews (registered users only) |
| Recommendation | CF/CBF results stored per user/guest |

---

## API Endpoints

| Method | Route | Who | What |
|---|---|---|---|
| POST | `/api/register` | Anyone | Create account |
| POST | `/api/login` | Anyone | Login |
| POST | `/api/logout` | Anyone | Clear session |
| POST | `/api/guest` | Anyone | Start guest session |
| POST | `/api/preferences` | Registered | Save plant preferences |
| POST | `/api/environment` | Registered | Save room conditions |
| POST | `/api/interact` | User or Guest | Log view/click/save |
| POST | `/api/rate` | Registered | Rate a plant 1-5 |
| POST | `/api/review` | Registered | Write a text review |
| POST | `/api/recommend` | User or Guest | Generate recommendations |
| GET | `/api/recommendations` | User or Guest | Get stored recommendations |
| GET | `/api/plants` | Anyone | Get all plants |
| GET | `/api/plants/<id>` | Anyone | Get one plant |

---

## Recommendation Logic

### Registered User → CF (Item-Item Cosine Similarity)
1. Fetch all ratings from Rating table
2. Build user-item matrix
3. Compute cosine similarity between plant columns
4. Predict scores for plants the user hasn't rated
5. Rank by predicted score
6. Store top 10 in Recommendation table

### Guest → CF Average Rating Fallback
1. If enough ratings exist (≥5): rank plants by average rating score
2. If not: fall back to most interacted plants (interaction count)
3. If no interactions: return first 10 plants from database
4. Store results in Recommendation table with guest_id

---

## Using Kaggle CSV Files

Drop any of these into the `data/` folder:
- `house_plant_species.csv`
- `plants_growth_care.csv`
- `indoor_plant_health.csv`

The preprocessor automatically maps column names to the schema.
If no CSVs found, 60 sample plants are loaded automatically.

---

## For Bishesh (Backend Developer)

All functions you need are in `app/db_utils.py`. Import them like:

```python
from app import db_utils

# Register
result = db_utils.register_user(name, email, password, experience_level)

# Login
result = db_utils.login_user(email, password)

# Guest
result = db_utils.create_guest_session()

# Preferences
result = db_utils.save_user_preference(user_id, light, maintenance, size, pet_friendly)

# Environment
result = db_utils.save_environment(user_id, light_level, humidity, temperature, room_size)

# Interaction
result = db_utils.log_interaction(plant_id, interaction_type, user_id=None, guest_id=None)

# Rating
result = db_utils.submit_rating(user_id, plant_id, rating_value)

# Review
result = db_utils.submit_review(user_id, plant_id, review_text)

# Generate Recommendations
result = db_utils.generate_cf_recommendation(user_id)       # registered user
result = db_utils.generate_guest_recommendation(guest_id)   # guest

# Retrieve stored recommendations
result = db_utils.get_recommendations(user_id=user_id)
result = db_utils.get_recommendations(guest_id=guest_id)

# Plants
result = db_utils.get_all_plants()
result = db_utils.get_plant_by_id(plant_id)
```

All functions return `{"success": True/False, ...}` — always check `success` before using data.
