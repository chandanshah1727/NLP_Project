"""Waste mapping and segregation decision rules."""
from backend.config import WASTE_MAPPING

def waste_info(category: str) -> dict:
    key = category.strip().lower()
    if key not in WASTE_MAPPING:
        raise ValueError("Invalid waste category")
    return WASTE_MAPPING[key]

def is_correct(category: str, selected_bin: str) -> bool:
    return selected_bin.strip() == waste_info(category)["bin"]
