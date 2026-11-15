"""Validated request payloads."""
from pydantic import BaseModel, Field, field_validator
from backend.config import CAMPUS_LOCATIONS, WASTE_CATEGORIES

class RecordCreate(BaseModel):
    waste_category: str
    confidence: float = Field(ge=0, le=100)
    location: str
    selected_bin: str = Field(min_length=1, max_length=80)
    notes: str | None = Field(default=None, max_length=500)
    weight_kg: float | None = Field(default=None, ge=0)
    image_filename: str | None = Field(default=None, max_length=255)
    @field_validator("waste_category")
    @classmethod
    def check_category(cls, value):
        value = value.strip().lower()
        if value not in WASTE_CATEGORIES: raise ValueError("Invalid waste category")
        return value
    @field_validator("location")
    @classmethod
    def check_location(cls, value):
        if value not in CAMPUS_LOCATIONS: raise ValueError("Invalid campus location")
        return value

class RecordUpdate(BaseModel):
    location: str | None = None
    selected_bin: str | None = Field(default=None, min_length=1, max_length=80)
    notes: str | None = Field(default=None, max_length=500)
    weight_kg: float | None = Field(default=None, ge=0)
    @field_validator("location")
    @classmethod
    def check_location(cls, value):
        if value is None: raise ValueError("Campus location cannot be empty")
        if value is not None and value not in CAMPUS_LOCATIONS: raise ValueError("Invalid campus location")
        return value

    @field_validator("selected_bin")
    @classmethod
    def check_selected_bin(cls, value):
        if value is None: raise ValueError("Selected bin cannot be empty")
        return value.strip()
