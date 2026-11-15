"""Shared, configurable waste and campus policy."""

from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "best_efficientnetb0_finetuned.keras"
CLASS_PATH = BASE_DIR / "models" / "class_names.json"
IMAGE_SIZE = (224, 224)
MAX_IMAGE_BYTES = 10 * 1024 * 1024
CAMPUS_LOCATIONS = ["Hostel", "Canteen", "Academic Block", "Library"]
WASTE_MAPPING = {
    "battery": {"type": "E-waste", "bin": "E-waste Collection", "guidance": "Keep batteries separate and take them to the designated e-waste collection point."},
    "cardboard": {"type": "Recyclable", "bin": "Recyclable", "guidance": "Keep cardboard clean and dry; flatten large boxes where practical."},
    "glass": {"type": "Recyclable", "bin": "Recyclable", "guidance": "Use the campus recyclable stream. Handle broken glass safely and follow local instructions."},
    "metal": {"type": "Recyclable", "bin": "Recyclable", "guidance": "Empty containers before placing them in the recyclable stream."},
    "organic": {"type": "Biodegradable", "bin": "Biodegradable", "guidance": "Place food and other accepted organic waste in the biodegradable stream."},
    "paper": {"type": "Recyclable", "bin": "Recyclable", "guidance": "Keep paper dry and free of food contamination for recycling."},
    "plastic": {"type": "Recyclable", "bin": "Recyclable", "guidance": "Empty containers and follow campus rules for accepted plastics."},
    "textile": {"type": "Special Collection", "bin": "Textile Collection", "guidance": "Textile acceptance varies. Use the designated collection only when the item is accepted by campus policy."},
    "trash": {"type": "Residual Waste", "bin": "Residual Waste", "guidance": "Use residual waste only when the item is not accepted in recycling, organic, or special collection streams."},
}
WASTE_CATEGORIES = list(WASTE_MAPPING)
SELECTABLE_BINS = sorted({v["bin"] for v in WASTE_MAPPING.values()} | {"Other / Unsure"})

with CLASS_PATH.open(encoding="utf-8") as _f:
    MODEL_CLASSES = json.load(_f)
