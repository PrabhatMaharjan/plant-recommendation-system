"""
Fetches plant images from Unsplash
Run this ONCE after preprocess_plants.py to add images to all plants.
python scripts/fetch_plant_images.py
"""

import os
import sys
import requests
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import db, Plant

# Paste your Unsplash Access Key here
UNSPLASH_ACCESS_KEY = "4y7z0WhFO5Tr8BA9nHpsVVXCEHbO04Xcw0ctCVLpF68"

UNSPLASH_URL = "https://api.unsplash.com/search/photos"


def fetch_image_url(plant_name: str) -> str:
    try:
        response = requests.get(
            UNSPLASH_URL,
            params={
                "query": f"{plant_name} indoor plant",
                "per_page": 1,
                "orientation": "squarish"
            },
            headers={
                "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
            },
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            results = data.get("results", [])
            if results:
                return results[0]["urls"]["regular"]
        return None

    except Exception as e:
        print(f"   Error fetching image for {plant_name}: {e}")
        return None


def fetch_all_plant_images():
    app = create_app()

    with app.app_context():
        print("\n🌿 Fetching Plant Images from Unsplash")
        print("=" * 50)

        plants = Plant.query.all()
        total = len(plants)
        updated = 0
        skipped = 0
        failed = 0

        for i, plant in enumerate(plants, start=1):
            if plant.image_url:
                skipped += 1
                continue

            print(f"   [{i}/{total}] Fetching: {plant.plant_name}")

            image_url = fetch_image_url(plant.plant_name)

            if image_url:
                plant.image_url = image_url
                db.session.commit()
                updated += 1
                print(f"   ✅ Got image for {plant.plant_name}")
            else:
                failed += 1
                print(f"   ❌ No image found for {plant.plant_name}")

            time.sleep(0.5)

        print("\n" + "=" * 50)
        print(f"   Total plants: {total}")
        print(f"   Images added: {updated}")
        print(f"   Already had image: {skipped}")
        print(f"   No image found: {failed}")
        print("\n✅ Image fetching complete!")


if __name__ == "__main__":
    fetch_all_plant_images()