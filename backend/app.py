"""FastAPI application for waste prediction, records, analytics, and alerts."""
from datetime import date, datetime, timedelta
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import String, cast, or_
from sqlalchemy import text
from backend.database import create_tables, SessionLocal, WasteRecord
from backend.config import CAMPUS_LOCATIONS, WASTE_CATEGORIES, WASTE_MAPPING, MAX_IMAGE_BYTES, MODEL_PATH
from backend.schemas import RecordCreate, RecordUpdate
from backend.services.prediction_service import predict_image
from backend.services.waste_service import is_correct
from backend.services.analytics_service import filtered_records, summarize, location_stats, trend_stats
from backend.services.alert_service import generate_alerts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
create_tables()
app = FastAPI(title="Smart Waste Segregation API", version="1.0.0", description="Campus waste classification and segregation monitoring API.")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"], allow_credentials=False, allow_methods=["GET", "POST", "PUT", "DELETE"], allow_headers=["*"])

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

def serialize(record: WasteRecord) -> dict:
    recommended = WASTE_MAPPING.get(record.waste_category, {}).get("bin")
    return {"id": record.id, "waste_category": record.waste_category, "waste_type": record.waste_type,
            "confidence": record.confidence, "location": record.location, "selected_bin": record.selected_bin,
            "recommended_bin": recommended, "is_correctly_segregated": bool(record.is_correctly_segregated),
            "correct_segregation": bool(record.is_correctly_segregated), "created_at": record.created_at.isoformat() if record.created_at else None,
            "notes": record.notes, "weight_kg": record.weight_kg, "image_filename": record.image_filename}

def parse_filters(start: date | None, end: date | None, location: str | None, category: str | None):
    if start and end and start > end: raise HTTPException(422, "Start date must be on or before end date")
    if location and location not in CAMPUS_LOCATIONS: raise HTTPException(422, "Invalid campus location")
    if category and category not in WASTE_CATEGORIES: raise HTTPException(422, "Invalid waste category")

@app.get("/")
def home():
    database_connected = False
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        database_connected = True
    except SQLAlchemyError:
        logger.exception("Database health check failed")
    return {"status": "ok", "message": "Smart Waste Segregation API is running",
            "model_configured": MODEL_PATH.is_file(), "database_connected": database_connected}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    if file.content_type not in {"image/jpeg", "image/png", "image/webp", "image/jpg"}:
        raise HTTPException(415, "Upload a JPG, PNG, or WEBP image")
    data = await file.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES: raise HTTPException(413, "Image exceeds the 10 MB upload limit")
    try: return predict_image(data)
    except ValueError as exc: raise HTTPException(400, str(exc)) from exc
    except Exception as exc:
        logger.exception("Prediction failed")
        raise HTTPException(503, "Prediction service is currently unavailable") from exc

@app.post("/records", status_code=201)
def create_record(payload: RecordCreate, db: Session = Depends(get_db)):
    info = WASTE_MAPPING[payload.waste_category]
    record = WasteRecord(**payload.model_dump(), waste_type=info["type"], is_correctly_segregated=int(is_correct(payload.waste_category, payload.selected_bin)))
    try:
        db.add(record); db.commit(); db.refresh(record)
        return {"message": "Waste record saved", "record_id": record.id, "record": serialize(record)}
    except SQLAlchemyError as exc:
        db.rollback(); logger.exception("Could not save waste record")
        raise HTTPException(500, "Could not save waste record") from exc

@app.get("/records")
def get_records(start: date | None = None, end: date | None = None, location: str | None = None,
                category: str | None = None, status: str | None = Query(default=None, pattern="^(correct|incorrect)$"),
                search: str | None = None, limit: int = Query(100, ge=1, le=500), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    parse_filters(start, end, location, category)
    query = db.query(WasteRecord)
    if start: query = query.filter(WasteRecord.created_at >= datetime.combine(start, datetime.min.time()))
    if end: query = query.filter(WasteRecord.created_at < datetime.combine(end + timedelta(days=1), datetime.min.time()))
    if location: query = query.filter(WasteRecord.location == location)
    if category: query = query.filter(WasteRecord.waste_category == category)
    if status: query = query.filter(WasteRecord.is_correctly_segregated == int(status == "correct"))
    if search:
        term = search.casefold()
        query = query.filter(or_(cast(WasteRecord.id, String).ilike(f"%{term}%"), WasteRecord.waste_category.ilike(f"%{term}%"),
                                 WasteRecord.location.ilike(f"%{term}%"), WasteRecord.selected_bin.ilike(f"%{term}%")))
    total = query.count()
    records = query.order_by(WasteRecord.created_at.desc()).offset(offset).limit(limit).all()
    return {"items": [serialize(r) for r in records], "total": total, "limit": limit, "offset": offset}

@app.get("/records/{record_id}")
def get_record(record_id: int, db: Session = Depends(get_db)):
    record = db.get(WasteRecord, record_id)
    if not record: raise HTTPException(404, "Waste record not found")
    return serialize(record)

@app.put("/records/{record_id}")
def update_record(record_id: int, payload: RecordUpdate, db: Session = Depends(get_db)):
    record = db.get(WasteRecord, record_id)
    if not record: raise HTTPException(404, "Waste record not found")
    for key, value in payload.model_dump(exclude_unset=True).items(): setattr(record, key, value)
    record.is_correctly_segregated = int(is_correct(record.waste_category, record.selected_bin or ""))
    try: db.commit(); db.refresh(record)
    except SQLAlchemyError as exc:
        db.rollback(); logger.exception("Could not update waste record")
        raise HTTPException(500, "Could not update waste record") from exc
    return {"message": "Waste record updated", "record": serialize(record)}

@app.delete("/records/{record_id}", status_code=204)
def delete_record(record_id: int, db: Session = Depends(get_db)):
    record = db.get(WasteRecord, record_id)
    if not record: raise HTTPException(404, "Waste record not found")
    db.delete(record); db.commit()

@app.get("/analytics/summary")
def analytics_summary(start: date | None = None, end: date | None = None, location: str | None = None, category: str | None = None, db: Session = Depends(get_db)):
    parse_filters(start, end, location, category)
    return summarize(filtered_records(db, start, end, location, category))

@app.get("/analytics/locations")
def analytics_locations(start: date | None = None, end: date | None = None, category: str | None = None, db: Session = Depends(get_db)):
    parse_filters(start, end, None, category)
    return location_stats(filtered_records(db, start, end, category=category))

@app.get("/analytics/categories")
def analytics_categories(start: date | None = None, end: date | None = None, location: str | None = None, category: str | None = None, db: Session = Depends(get_db)):
    parse_filters(start, end, location, category)
    records = filtered_records(db, start, end, location, category)
    return {"categories": summarize(records)["category_distribution"], "types": summarize(records)["type_distribution"]}

@app.get("/analytics/trends")
def analytics_trends(days: int = Query(30, ge=1, le=365), start: date | None = None, end: date | None = None, location: str | None = None, category: str | None = None, db: Session = Depends(get_db)):
    parse_filters(start, end, location, category)
    return trend_stats(filtered_records(db, start, end, location, category), days, start, end)

@app.get("/alerts")
def alerts(location: str | None = None, severity: str | None = Query(default=None, pattern="^(low|medium|high)$"), db: Session = Depends(get_db)):
    if location and location not in CAMPUS_LOCATIONS: raise HTTPException(422, "Invalid campus location")
    records = filtered_records(db, location=location)
    result = generate_alerts(records)
    if location: result = [a for a in result if a["location"] in (location, "All locations")]
    if severity: result = [a for a in result if a["severity"] == severity]
    return {"alerts": result, "count": len(result), "threshold_percentage": 70}
