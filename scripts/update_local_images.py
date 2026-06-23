"""
update_local_images.py - Maps local image files to plants in database
Database Manager: Prabhat Maharjan (0371462)
Group 13 - Indoor Plant Recommendation System

Run this AFTER images are in app/static/images/plants/ folder.

Usage:
    python scripts/update_local_images.py
"""

import os
import sys
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.models import db, Plant

IMAGES_FOLDER = os.path.join(
    os.path.dirname(__file__), "..", "app", "static", "images", "plants"
)

IMAGE_BASE_URL = "/static/images/plants/"


def plant_name_to_filename(plant_name):
    name = plant_name.lower().strip()
    name_no_brackets = re.sub(r'\s*\(.*?\)', '', name).strip()

    def to_filename(n):
        n = re.sub(r'[^a-z0-9\s]', '', n)
        n = re.sub(r'\s+', '_', n)
        n = re.sub(r'_+', '_', n)
        n = n.strip('_')
        return n

    base = to_filename(name)
    base_no_brackets = to_filename(name_no_brackets)

    extensions = [".jpg", ".png", ".jpeg", ".JPG", ".PNG", ".JPEG"]
    filenames = []

    for ext in extensions:
        filenames.append(base + ext)
        if base_no_brackets != base:
            filenames.append(base_no_brackets + ext)

    return filenames


def update_local_images():
    app = create_app()

    with app.app_context():
        print("\n🌿 Updating Plant Images from Local Files")
        print("=" * 50)

        if not os.path.exists(IMAGES_FOLDER):
            print(f"\nImages folder not found:")
            print(f"   {IMAGES_FOLDER}")
            print(f"\nPlease create this folder first:")
            print(f"   app/static/images/plants/")
            return

        image_files = set(os.listdir(IMAGES_FOLDER))
        print(f"   Found {len(image_files)} image files in folder")

        if not image_files:
            print("\nNo image files found in the folder.")
            return

        plants = Plant.query.all()
        total = len(plants)
        updated = 0
        not_found = 0
        already_local = 0
        not_found_plants = []

        print(f"   Total plants in database: {total}")
        print(f"\n   Processing plants...")
        print("-" * 50)

        for plant in plants:
            if plant.image_url and plant.image_url.startswith("/static/"):
                already_local += 1
                continue

            possible_filenames = plant_name_to_filename(plant.plant_name)

            found_file = None
            for filename in possible_filenames:
                if filename in image_files:
                    found_file = filename
                    break

            if found_file:
                local_path = IMAGE_BASE_URL + found_file
                plant.image_url = local_path
                db.session.commit()
                updated += 1
                print(f"   OK {plant.plant_name} -> {local_path}")
            else:
                not_found += 1
                not_found_plants.append(plant.plant_name)

        print("\n" + "=" * 50)
        print(f"   Total plants:           {total}")
        print(f"   Updated to local path:  {updated}")
        print(f"   Already local:          {already_local}")
        print(f"   Image file not found:   {not_found}")

        if not_found_plants:
            print(f"\n   Plants with no matching image file:")
            for name in not_found_plants:
                possible = plant_name_to_filename(name)
                print(f"   - {name}")
                print(f"     name your file: {possible[0]}")

        print("\nDone!")
        print(f"\n   Images served from:")
        print(f"   http://localhost:5000/static/images/plants/")


if __name__ == "__main__":
    update_local_images()