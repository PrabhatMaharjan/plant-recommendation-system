"""
preprocess_plants.py - Data Preprocessing & Loading Script
Database Manager: Prabhat Maharjan (0371462)
Group 13 - Indoor Plant Recommendation System

Run this script ONCE after init to load Kaggle CSV data into the database.

Usage:
    python scripts/preprocess_plants.py

Place your Kaggle CSV files in the data/ folder before running.
Supported file names (any of these will be picked up automatically):
  - house_plant_species.csv
  - plants_growth_care.csv
  - indoor_plant_health.csv
"""

import os
import sys
import pandas as pd

# Add project root to path so imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import db, PlantCategory, Plant

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


# ─────────────────────────────────────────────
# STANDARDIZATION HELPERS
# ─────────────────────────────────────────────

def standardize_light(val: str) -> str:
    """Maps various raw light values → Low / Medium / High"""
    if pd.isna(val):
        return "Medium"
    val = str(val).strip().lower()
    high_keywords = ["bright", "full sun", "direct sun", "high", "full light"]
    medium_keywords = ["indirect", "partial", "medium", "filtered", "moderate"]
    for kw in high_keywords:
        if kw in val:
            return "High"
    for kw in medium_keywords:
        if kw in val:
            return "Medium"
    return "Low"


def standardize_maintenance(val: str) -> str:
    """Maps various maintenance/care values → Low / Medium / High"""
    if pd.isna(val):
        return "Medium"
    val = str(val).strip().lower()
    low_kw = ["easy", "low effort", "low", "minimal", "simple", "beginner"]
    high_kw = ["high", "difficult", "expert", "demanding", "complex"]
    for kw in low_kw:
        if kw in val:
            return "Low"
    for kw in high_kw:
        if kw in val:
            return "High"
    return "Medium"


def standardize_toxicity(val) -> str:
    """Maps toxicity values → Non-toxic / Mildly toxic / Toxic"""
    if pd.isna(val):
        return "Non-toxic"
    val_str = str(val).strip().lower()
    # Handle boolean-ish values
    if val_str in ["true", "1", "yes", "toxic", "poisonous", "dangerous"]:
        return "Toxic"
    if val_str in ["mild", "mildly", "slightly", "moderate"]:
        return "Mildly toxic"
    return "Non-toxic"


def standardize_watering(val: str) -> str:
    """Maps watering frequency → Daily / Weekly / Bi-weekly"""
    if pd.isna(val):
        return "Weekly"
    val = str(val).strip().lower()
    if "daily" in val or "frequent" in val or "often" in val:
        return "Daily"
    if "bi" in val or "fortnight" in val or "two" in val or "rare" in val or "infrequent" in val:
        return "Bi-weekly"
    return "Weekly"


def standardize_size(val: str) -> str:
    """Maps size values → Small / Medium / Large"""
    if pd.isna(val):
        return "Medium"
    val = str(val).strip().lower()
    if any(k in val for k in ["small", "mini", "compact", "tiny"]):
        return "Small"
    if any(k in val for k in ["large", "tall", "big", "tree"]):
        return "Large"
    return "Medium"


def standardize_growth(val: str) -> str:
    """Maps growth rate → Slow / Moderate / Fast"""
    if pd.isna(val):
        return "Moderate"
    val = str(val).strip().lower()
    if "slow" in val:
        return "Slow"
    if "fast" in val or "rapid" in val or "quick" in val:
        return "Fast"
    return "Moderate"


def standardize_humidity(val: str) -> str:
    """Maps humidity → Low / Medium / High"""
    if pd.isna(val):
        return "Medium"
    val = str(val).strip().lower()
    if any(k in val for k in ["high", "humid", "tropical", "wet"]):
        return "High"
    if any(k in val for k in ["low", "dry", "arid", "desert"]):
        return "Low"
    return "Medium"


def standardize_temperature(val: str) -> str:
    """Maps temperature → Cool / Moderate / Warm"""
    if pd.isna(val):
        return "Moderate"
    val = str(val).strip().lower()
    if any(k in val for k in ["cool", "cold", "low"]):
        return "Cool"
    if any(k in val for k in ["warm", "hot", "tropical", "high"]):
        return "Warm"
    return "Moderate"


# ─────────────────────────────────────────────
# CSV LOADING & COLUMN MAPPING
# ─────────────────────────────────────────────

def load_csv_files() -> pd.DataFrame:
    """
    Loads whichever Kaggle CSVs are present in data/ folder.
    Normalizes column names to a standard format.
    Returns a combined DataFrame.
    """
    frames = []

    # Possible column name mappings for different Kaggle datasets
    COLUMN_MAP = {
        # plant name
        "common name": "plant_name",
        "plant name": "plant_name",
        "name": "plant_name",
        "species": "plant_name",
        "plant_name": "plant_name",

        # category
        "type": "category_name",
        "plant type": "category_name",
        "category": "category_name",
        "family": "category_name",
        "category_name": "category_name",

        # light
        "light": "light_requirement",
        "sunlight": "light_requirement",
        "light requirement": "light_requirement",
        "light requirements": "light_requirement",
        "light_requirement": "light_requirement",

        # watering
        "watering": "watering_frequency",
        "water": "watering_frequency",
        "watering frequency": "watering_frequency",
        "watering_frequency": "watering_frequency",

        # maintenance
        "care": "maintenance_level",
        "difficulty": "maintenance_level",
        "maintenance": "maintenance_level",
        "care level": "maintenance_level",
        "maintenance_level": "maintenance_level",

        # humidity
        "humidity": "humidity_requirement",
        "humidity requirement": "humidity_requirement",
        "humidity_requirement": "humidity_requirement",

        # temperature
        "temperature": "temperature_range",
        "temp": "temperature_range",
        "temperature range": "temperature_range",
        "temperature_range": "temperature_range",

        # toxicity
        "toxic": "toxicity_level",
        "toxicity": "toxicity_level",
        "poisonous": "toxicity_level",
        "toxicity_level": "toxicity_level",

        # growth
        "growth rate": "growth_rate",
        "growth": "growth_rate",
        "growth_rate": "growth_rate",

        # size
        "size": "size_category",
        "plant size": "size_category",
        "size_category": "size_category",
    }

    csv_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".csv")]
    if not csv_files:
        print("⚠  No CSV files found in data/ folder.")
        print("   Generating sample plant data instead...")
        return _generate_sample_data()

    for fname in csv_files:
        fpath = os.path.join(DATA_DIR, fname)
        try:
            df = pd.read_csv(fpath, encoding="utf-8", on_bad_lines="skip")
        except Exception:
            try:
                df = pd.read_csv(fpath, encoding="latin-1", on_bad_lines="skip")
            except Exception as e:
                print(f"   Could not read {fname}: {e}")
                continue

        # Normalize column names
        df.columns = [c.strip().lower() for c in df.columns]
        df = df.rename(columns={k: v for k, v in COLUMN_MAP.items() if k in df.columns})
        frames.append(df)
        print(f"   Loaded {fname}: {len(df)} rows")

    if not frames:
        print("   No valid CSVs loaded — using sample data.")
        return _generate_sample_data()

    combined = pd.concat(frames, ignore_index=True)
    return combined


def _generate_sample_data() -> pd.DataFrame:
    """
    Generates 60 sample indoor plants if no Kaggle CSVs are available.
    Ensures the system can run and be demonstrated without external data.
    """
    plants = [
        # (name, category, light, watering, maintenance, humidity, temp, toxicity, growth, size)
        ("Peace Lily", "Tropical", "Low", "Weekly", "Low", "High", "Moderate", "Mildly toxic", "Moderate", "Medium"),
        ("Snake Plant", "Succulent", "Low", "Bi-weekly", "Low", "Low", "Warm", "Mildly toxic", "Slow", "Medium"),
        ("Pothos", "Vine", "Low", "Weekly", "Low", "Medium", "Moderate", "Mildly toxic", "Fast", "Medium"),
        ("Spider Plant", "Tropical", "Medium", "Weekly", "Low", "Medium", "Moderate", "Non-toxic", "Fast", "Small"),
        ("ZZ Plant", "Tropical", "Low", "Bi-weekly", "Low", "Low", "Warm", "Toxic", "Slow", "Medium"),
        ("Fiddle Leaf Fig", "Tree", "High", "Weekly", "High", "Medium", "Warm", "Mildly toxic", "Moderate", "Large"),
        ("Monstera Deliciosa", "Tropical", "Medium", "Weekly", "Medium", "High", "Warm", "Mildly toxic", "Fast", "Large"),
        ("Rubber Plant", "Tree", "Medium", "Weekly", "Medium", "Medium", "Moderate", "Mildly toxic", "Moderate", "Large"),
        ("Aloe Vera", "Succulent", "High", "Bi-weekly", "Low", "Low", "Warm", "Mildly toxic", "Slow", "Small"),
        ("Boston Fern", "Fern", "Medium", "Weekly", "Medium", "High", "Cool", "Non-toxic", "Moderate", "Medium"),
        ("Calathea", "Tropical", "Low", "Weekly", "High", "High", "Moderate", "Non-toxic", "Slow", "Small"),
        ("Chinese Evergreen", "Tropical", "Low", "Weekly", "Low", "Medium", "Moderate", "Mildly toxic", "Slow", "Medium"),
        ("Dracaena", "Tree", "Medium", "Weekly", "Low", "Medium", "Moderate", "Toxic", "Slow", "Large"),
        ("English Ivy", "Vine", "Medium", "Weekly", "Medium", "Medium", "Cool", "Toxic", "Fast", "Small"),
        ("Jade Plant", "Succulent", "High", "Bi-weekly", "Low", "Low", "Moderate", "Toxic", "Slow", "Small"),
        ("Lucky Bamboo", "Tropical", "Medium", "Weekly", "Low", "Medium", "Moderate", "Non-toxic", "Moderate", "Small"),
        ("Parlor Palm", "Palm", "Low", "Weekly", "Low", "Medium", "Moderate", "Non-toxic", "Slow", "Medium"),
        ("Philodendron", "Tropical", "Medium", "Weekly", "Low", "Medium", "Moderate", "Toxic", "Fast", "Medium"),
        ("Ponytail Palm", "Palm", "High", "Bi-weekly", "Low", "Low", "Warm", "Non-toxic", "Slow", "Medium"),
        ("Prayer Plant", "Tropical", "Low", "Weekly", "Medium", "High", "Moderate", "Non-toxic", "Moderate", "Small"),
        ("Orchid", "Flower", "Medium", "Weekly", "High", "High", "Moderate", "Non-toxic", "Slow", "Small"),
        ("African Violet", "Flower", "Medium", "Weekly", "Medium", "Medium", "Moderate", "Non-toxic", "Moderate", "Small"),
        ("Anthurium", "Tropical", "Medium", "Weekly", "Medium", "High", "Warm", "Toxic", "Moderate", "Small"),
        ("Bird of Paradise", "Tropical", "High", "Weekly", "Medium", "Medium", "Warm", "Mildly toxic", "Moderate", "Large"),
        ("Bromeliad", "Tropical", "Medium", "Weekly", "Low", "High", "Warm", "Non-toxic", "Slow", "Small"),
        ("Cactus (Barrel)", "Cactus", "High", "Bi-weekly", "Low", "Low", "Warm", "Non-toxic", "Slow", "Small"),
        ("Cactus (Christmas)", "Cactus", "Medium", "Weekly", "Low", "Medium", "Moderate", "Non-toxic", "Slow", "Small"),
        ("Cast Iron Plant", "Tropical", "Low", "Bi-weekly", "Low", "Low", "Cool", "Non-toxic", "Slow", "Medium"),
        ("Croton", "Tropical", "High", "Weekly", "Medium", "High", "Warm", "Toxic", "Moderate", "Medium"),
        ("Cyclamen", "Flower", "Medium", "Weekly", "Medium", "Medium", "Cool", "Toxic", "Moderate", "Small"),
        ("Dieffenbachia", "Tropical", "Medium", "Weekly", "Medium", "Medium", "Moderate", "Toxic", "Moderate", "Medium"),
        ("Dwarf Umbrella", "Tree", "Medium", "Weekly", "Low", "Medium", "Moderate", "Mildly toxic", "Moderate", "Medium"),
        ("Echeveria", "Succulent", "High", "Bi-weekly", "Low", "Low", "Warm", "Non-toxic", "Slow", "Small"),
        ("Elephant Ear", "Tropical", "Medium", "Weekly", "Medium", "High", "Warm", "Toxic", "Fast", "Large"),
        ("False Shamrock", "Tropical", "Medium", "Weekly", "Low", "Medium", "Moderate", "Mildly toxic", "Moderate", "Small"),
        ("Gerbera Daisy", "Flower", "High", "Weekly", "Medium", "Medium", "Moderate", "Non-toxic", "Moderate", "Small"),
        ("Haworthia", "Succulent", "Medium", "Bi-weekly", "Low", "Low", "Moderate", "Non-toxic", "Slow", "Small"),
        ("Heartleaf Philodendron", "Vine", "Low", "Weekly", "Low", "Medium", "Moderate", "Toxic", "Fast", "Medium"),
        ("Inch Plant", "Vine", "Medium", "Weekly", "Low", "Medium", "Moderate", "Mildly toxic", "Fast", "Small"),
        ("Kentia Palm", "Palm", "Low", "Weekly", "Low", "Medium", "Moderate", "Non-toxic", "Slow", "Large"),
        ("Lavender", "Herb", "High", "Weekly", "Medium", "Low", "Cool", "Non-toxic", "Moderate", "Small"),
        ("Lemon Tree (Dwarf)", "Tree", "High", "Weekly", "High", "Medium", "Warm", "Mildly toxic", "Moderate", "Medium"),
        ("Majesty Palm", "Palm", "Medium", "Weekly", "Medium", "High", "Moderate", "Non-toxic", "Moderate", "Large"),
        ("Mint", "Herb", "High", "Daily", "Low", "Medium", "Cool", "Non-toxic", "Fast", "Small"),
        ("Money Tree", "Tree", "Medium", "Weekly", "Low", "Medium", "Moderate", "Non-toxic", "Moderate", "Medium"),
        ("Norfolk Island Pine", "Tree", "High", "Weekly", "Medium", "Medium", "Cool", "Mildly toxic", "Slow", "Large"),
        ("Panda Plant", "Succulent", "High", "Bi-weekly", "Low", "Low", "Moderate", "Mildly toxic", "Slow", "Small"),
        ("Peperomia", "Tropical", "Medium", "Bi-weekly", "Low", "Medium", "Moderate", "Non-toxic", "Slow", "Small"),
        ("Polka Dot Plant", "Flower", "Medium", "Weekly", "Medium", "High", "Moderate", "Non-toxic", "Moderate", "Small"),
        ("Purple Passion Plant", "Vine", "High", "Weekly", "Medium", "Medium", "Moderate", "Non-toxic", "Fast", "Small"),
        ("Rex Begonia", "Flower", "Medium", "Weekly", "Medium", "High", "Moderate", "Mildly toxic", "Moderate", "Small"),
        ("Rosemary", "Herb", "High", "Weekly", "Medium", "Low", "Moderate", "Non-toxic", "Moderate", "Small"),
        ("Schefflera", "Tree", "Medium", "Weekly", "Low", "Medium", "Moderate", "Mildly toxic", "Moderate", "Large"),
        ("Sedum", "Succulent", "High", "Bi-weekly", "Low", "Low", "Moderate", "Non-toxic", "Slow", "Small"),
        ("Silver Pothos", "Vine", "Medium", "Weekly", "Low", "Medium", "Moderate", "Mildly toxic", "Fast", "Medium"),
        ("String of Pearls", "Succulent", "High", "Bi-weekly", "Medium", "Low", "Moderate", "Toxic", "Moderate", "Small"),
        ("Ti Plant", "Tropical", "Medium", "Weekly", "Medium", "Medium", "Warm", "Toxic", "Moderate", "Large"),
        ("Tradescantia", "Vine", "Medium", "Weekly", "Low", "Medium", "Moderate", "Mildly toxic", "Fast", "Small"),
        ("Venus Fly Trap", "Carnivorous", "High", "Daily", "High", "High", "Moderate", "Non-toxic", "Slow", "Small"),
        ("Yucca", "Tree", "High", "Bi-weekly", "Low", "Low", "Warm", "Mildly toxic", "Slow", "Large"),
    ]

    df = pd.DataFrame(plants, columns=[
        "plant_name", "category_name", "light_requirement", "watering_frequency",
        "maintenance_level", "humidity_requirement", "temperature_range",
        "toxicity_level", "growth_rate", "size_category"
    ])
    return df


# ─────────────────────────────────────────────
# MAIN LOADING PROCEDURE
# ─────────────────────────────────────────────

def preprocess_and_load():
    app = create_app()

    with app.app_context():
        print("\n📋 Starting Data Preprocessing & Loading")
        print("=" * 50)

        df = load_csv_files()
        print(f"\n   Total rows to process: {len(df)}")

        # Ensure plant_name column exists
        if "plant_name" not in df.columns:
            # Try to find any string column that could be name
            str_cols = df.select_dtypes(include="object").columns.tolist()
            if str_cols:
                df = df.rename(columns={str_cols[0]: "plant_name"})
            else:
                print("❌ Cannot identify plant name column. Aborting.")
                return

        # Step 2: Remove duplicates and nulls
        df = df.drop_duplicates(subset=["plant_name"])
        df = df.dropna(subset=["plant_name"])
        df["plant_name"] = df["plant_name"].str.strip()
        df = df[df["plant_name"] != ""]
        print(f"   After dedup/null removal: {len(df)} plants")

        # Step 3: Fill missing category
        if "category_name" not in df.columns:
            df["category_name"] = "General"
        df["category_name"] = df["category_name"].fillna("General").str.strip()

        # Step 4: Fill NaN values before standardization
        df["light_requirement"] = df.get("light_requirement", pd.Series(["Medium"] * len(df))).fillna("Medium")
        df["maintenance_level"] = df.get("maintenance_level", pd.Series(["Medium"] * len(df))).fillna("Medium")
        df["toxicity_level"] = df.get("toxicity_level", pd.Series(["Non-toxic"] * len(df))).fillna("Non-toxic")
        df["watering_frequency"] = df.get("watering_frequency", pd.Series(["Weekly"] * len(df))).fillna("Weekly")
        df["size_category"] = df.get("size_category", pd.Series(["Medium"] * len(df))).fillna("Medium")
        df["growth_rate"] = df.get("growth_rate", pd.Series(["Moderate"] * len(df))).fillna("Moderate")
        df["humidity_requirement"] = df.get("humidity_requirement", pd.Series(["Medium"] * len(df))).fillna("Medium")
        df["temperature_range"] = df.get("temperature_range", pd.Series(["Moderate"] * len(df))).fillna("Moderate")

        # Standardize all attribute columns
        df["light_requirement"] = df["light_requirement"].apply(standardize_light)
        df["maintenance_level"] = df["maintenance_level"].apply(standardize_maintenance)
        df["toxicity_level"] = df["toxicity_level"].apply(standardize_toxicity)
        df["watering_frequency"] = df["watering_frequency"].apply(standardize_watering)
        df["size_category"] = df["size_category"].apply(standardize_size)
        df["growth_rate"] = df["growth_rate"].apply(standardize_growth)
        df["humidity_requirement"] = df["humidity_requirement"].apply(standardize_humidity)
        df["temperature_range"] = df["temperature_range"].apply(standardize_temperature)
        print("\n   Standardization complete.")

        # Step 5: Insert PlantCategories
        categories_inserted = 0
        unique_categories = df["category_name"].unique()
        for cat_name in unique_categories:
            existing = PlantCategory.query.filter_by(category_name=cat_name).first()
            if not existing:
                cat = PlantCategory(category_name=cat_name)
                db.session.add(cat)
                categories_inserted += 1
        db.session.commit()
        print(f"   Categories inserted: {categories_inserted}")

        # Step 6: Insert Plants
        plants_inserted = 0
        plants_skipped = 0
        for _, row in df.iterrows():
            existing = Plant.query.filter_by(plant_name=row["plant_name"]).first()
            if existing:
                plants_skipped += 1
                continue

            cat = PlantCategory.query.filter_by(category_name=row["category_name"]).first()
            if not cat:
                cat = PlantCategory(category_name=row["category_name"])
                db.session.add(cat)
                db.session.flush()

            plant = Plant(
                plant_name=row["plant_name"],
                category_id=cat.category_id,
                light_requirement=row["light_requirement"],
                watering_frequency=row["watering_frequency"],
                maintenance_level=row["maintenance_level"],
                humidity_requirement=row["humidity_requirement"],
                temperature_range=row["temperature_range"],
                toxicity_level=row["toxicity_level"],
                growth_rate=row["growth_rate"],
                size_category=row["size_category"]
            )
            db.session.add(plant)
            plants_inserted += 1

        db.session.commit()

        total = Plant.query.count()
        print(f"   Plants inserted: {plants_inserted}")
        print(f"   Plants skipped (already exist): {plants_skipped}")
        print(f"   Total plants in database: {total}")
        print("\n✅ Data loading complete!")


if __name__ == "__main__":
    preprocess_and_load()
