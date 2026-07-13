import json
from pathlib import Path

# Path to data folder
DATA_DIR = Path(__file__).parent


def load_json(filename):
    """Load a JSON file from the data folder."""
    with open(DATA_DIR / filename, "r", encoding="utf-8") as file:
        return json.load(file)


# Load data once when the server starts
crops_data = load_json("crops.json")
seasons_data = load_json("seasons.json")
tips_data = load_json("tips.json")


# -----------------------------
# Tool 1: Recommend Crop
# -----------------------------
def recommend_crop(soil_type: str):
    soil_type = soil_type.lower().strip()

    if soil_type in crops_data:
        return {
            "soil_type": soil_type,
            "recommended_crops": crops_data[soil_type]
        }

    return {
        "error": f"No crop recommendations found for '{soil_type}'."
    }


# -----------------------------
# Tool 2: Seasonal Crop
# -----------------------------
def seasonal_crop(season: str):
    season = season.lower().strip()

    if season in seasons_data:
        return {
            "season": season,
            "recommended_crops": seasons_data[season]
        }

    return {
        "error": f"No crops found for season '{season}'."
    }


# -----------------------------
# Tool 3: Crop Tips
# -----------------------------
def crop_tips(crop_name: str):
    crop_name = crop_name.lower().strip()

    if crop_name in tips_data:
        return {
            "crop": crop_name,
            "tip": tips_data[crop_name]
        }

    return {
        "error": f"No tips found for '{crop_name}'."
    }


# -----------------------------
# Tool 4: Available Soils
# -----------------------------
def available_soils():
    return {
        "available_soils": list(crops_data.keys())
    }