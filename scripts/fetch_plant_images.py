"""
fetch_plant_images.py - Fetches plant images from Wikimedia Commons
Run this ONCE after preprocess_plants.py:
python scripts/fetch_plant_images.py
"""

import os
import sys
import requests
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import db, Plant

WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"


def fetch_plant_image(plant_name: str) -> str:
    """
    Tries multiple sources to get a plant image URL.
    Order: Wikimedia Commons → Wikipedia
    """

    # Strategy 1: Wikimedia Commons direct search
    url = _search_wikimedia(plant_name)
    if url:
        return url

    # Strategy 2: Wikimedia Commons with "plant" added
    url = _search_wikimedia(f"{plant_name} plant")
    if url:
        return url

    # Strategy 3: Wikipedia page image
    url = _search_wikipedia(plant_name)
    if url:
        return url

    # Strategy 4: First word only (e.g. "Aloe" from "Aloe Vera")
    words = plant_name.split()
    if len(words) > 1:
        url = _search_wikimedia(words[0])
        if url:
            return url
        url = _search_wikipedia(words[0])
        if url:
            return url

    return None


def _search_wikimedia(search_term: str) -> str:
    """
    Searches Wikimedia Commons for plant images.
    """
    try:
        response = requests.get(
            WIKIMEDIA_API,
            params={
                "action": "query",
                "generator": "search",
                "gsrsearch": search_term,
                "gsrnamespace": 6,
                "prop": "imageinfo",
                "iiprop": "url|mime",
                "gsrlimit": 5,
                "format": "json"
            },
            headers={"User-Agent": "PlantRecommendationSystem/1.0"},
            timeout=15
        )

        if response.status_code != 200:
            return None

        data = response.json()
        pages = data.get("query", {}).get("pages", {})

        for page_id, page in pages.items():
            imageinfo = page.get("imageinfo", [])
            if imageinfo:
                url = imageinfo[0].get("url", "")
                mime = imageinfo[0].get("mime", "")
                # Only return actual image files
                if url and mime.startswith("image/") and not url.endswith(".svg"):
                    return url

        return None

    except Exception:
        return None


def _search_wikipedia(plant_name: str) -> str:
    """
    Gets the thumbnail image from a Wikipedia page.
    """
    try:
        # Search for the page
        search_response = requests.get(
            WIKIPEDIA_API,
            params={
                "action": "query",
                "list": "search",
                "srsearch": plant_name,
                "format": "json",
                "srlimit": 1
            },
            headers={"User-Agent": "PlantRecommendationSystem/1.0"},
            timeout=15
        )

        if search_response.status_code != 200:
            return None

        search_data = search_response.json()
        results = search_data.get("query", {}).get("search", [])

        if not results:
            return None

        page_title = results[0]["title"]

        # Get page image
        image_response = requests.get(
            WIKIPEDIA_API,
            params={
                "action": "query",
                "titles": page_title,
                "prop": "pageimages",
                "format": "json",
                "pithumbsize": 500
            },
            headers={"User-Agent": "PlantRecommendationSystem/1.0"},
            timeout=15
        )

        if image_response.status_code != 200:
            return None

        image_data = image_response.json()
        pages = image_data.get("query", {}).get("pages", {})

        for page_id, page_info in pages.items():
            thumbnail = page_info.get("thumbnail", {})
            if thumbnail and "source" in thumbnail:
                return thumbnail["source"]

        return None

    except Exception:
        return None


def fetch_all_plant_images():
    app = create_app()

    with app.app_context():
        print("\n🌿 Fetching Plant Images")
        print("   Sources: Wikimedia Commons + Wikipedia")
        print("=" * 50)

        plants = Plant.query.all()
        total = len(plants)
        updated = 0
        skipped = 0
        failed = 0
        failed_plants = []

        for i, plant in enumerate(plants, start=1):
            # Skip if image already exists
            if plant.image_url:
                skipped += 1
                continue

            print(f"   [{i}/{total}] {plant.plant_name}", end=" ... ", flush=True)

            image_url = fetch_plant_image(plant.plant_name)

            if image_url:
                plant.image_url = image_url
                db.session.commit()
                updated += 1
                print("✅")
            else:
                failed += 1
                failed_plants.append(plant.plant_name)
                print("❌")

            # Small delay to be respectful to servers
            time.sleep(0.3)

        print("\n" + "=" * 50)
        print(f"   Total plants:        {total}")
        print(f"   Images added:        {updated}")
        print(f"   Already had image:   {skipped}")
        print(f"   No image found:      {failed}")
        if (total - skipped) > 0:
            rate = round((updated / (total - skipped)) * 100)
            print(f"   Success rate:        {rate}%")

        if failed_plants:
            print(f"\n   Plants without images:")
            for name in failed_plants:
                print(f"   - {name}")

        print("\n✅ Image fetching complete!")


if __name__ == "__main__":
    fetch_all_plant_images()