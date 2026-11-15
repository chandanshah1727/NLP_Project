"""Lazy loader for the existing EfficientNet classifier."""
import io
import logging
from functools import lru_cache
import numpy as np
from PIL import Image, UnidentifiedImageError
from tensorflow.keras.models import load_model
from backend.config import MODEL_PATH, MODEL_CLASSES, IMAGE_SIZE, MAX_IMAGE_BYTES, WASTE_MAPPING

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_model():
    if not MODEL_PATH.is_file():
        raise RuntimeError("Configured prediction model is unavailable")
    # Keep preprocessing consistent with training: model contains Rescaling(scale=255),
    # so RGB pixels are normalized to [0,1] here before the model rescales them.
    return load_model(MODEL_PATH)

def predict_image(data: bytes) -> dict:
    if not data:
        raise ValueError("The uploaded image is empty")
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Image exceeds the 10 MB upload limit")
    try:
        with Image.open(io.BytesIO(data)) as source:
            source.verify()
        with Image.open(io.BytesIO(data)) as source:
            image = source.convert("RGB").resize(IMAGE_SIZE)
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValueError("Upload a valid JPG, PNG, or WEBP image") from exc
    array = np.asarray(image, dtype=np.float32) / 255.0
    predictions = np.asarray(get_model().predict(np.expand_dims(array, axis=0), verbose=0))[0]
    if len(predictions) != len(MODEL_CLASSES):
        raise RuntimeError("Model output does not match configured class names")
    index = int(np.argmax(predictions))
    category = MODEL_CLASSES[index].lower()
    if category not in WASTE_MAPPING:
        raise RuntimeError("Model predicted an unsupported category")
    info = WASTE_MAPPING[category]
    return {"predicted_class": category, "confidence": round(float(predictions[index]) * 100, 2),
            "recommended_bin": info["bin"], "waste_type": info["type"], "guidance": info["guidance"]}
