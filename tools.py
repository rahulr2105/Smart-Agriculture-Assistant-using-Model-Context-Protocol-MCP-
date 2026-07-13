import json
from pathlib import Path


DATA_FILE = Path(__file__).parent / "disease_data.json"


def load_disease_data():
    with open(DATA_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def detect_disease(symptom: str) -> dict:
    """
    Detect plant disease based on visible symptoms.
    Example symptom: yellow leaves
    """
    disease_data = load_disease_data()

    symptom = symptom.lower().strip()

    if symptom in disease_data:
        result = disease_data[symptom]
        return {
            "symptom": symptom,
            "disease": result["disease"],
            "solution": result["solution"]
        }

    return {
        "symptom": symptom,
        "disease": "Disease not found",
        "solution": "Please check the symptom spelling or consult an agriculture expert."
    }