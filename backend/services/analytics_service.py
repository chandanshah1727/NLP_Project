"""Database-backed analytics shared by API and report generation."""
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session
from backend.database import WasteRecord
from backend.config import CAMPUS_LOCATIONS, WASTE_MAPPING

def filtered_records(db: Session, start: date | None = None, end: date | None = None,
                    location: str | None = None, category: str | None = None):
    q = db.query(WasteRecord)
    if start: q = q.filter(WasteRecord.created_at >= datetime.combine(start, datetime.min.time()))
    if end: q = q.filter(WasteRecord.created_at < datetime.combine(end + timedelta(days=1), datetime.min.time()))
    if location: q = q.filter(WasteRecord.location == location)
    if category: q = q.filter(WasteRecord.waste_category == category)
    return q.order_by(WasteRecord.created_at.desc()).all()

def summarize(records: list[WasteRecord]) -> dict:
    total = len(records)
    correct = sum(r.is_correctly_segregated == 1 for r in records)
    category_counts = Counter(r.waste_category for r in records)
    type_counts = Counter(WASTE_MAPPING.get(r.waste_category, {}).get("type", "Unknown") for r in records)
    return {"total_records": total, "recyclable_records": sum(category_counts[c] for c in ("cardboard", "glass", "metal", "paper", "plastic")),
            "biodegradable_records": category_counts["organic"], "residual_records": category_counts["trash"],
            "correct_records": correct, "incorrect_records": total-correct,
            "compliance_percentage": round(correct * 100 / total, 2) if total else 0.0,
            "average_confidence": round(sum(r.confidence for r in records)/total, 2) if total else 0.0,
            "category_distribution": dict(category_counts), "type_distribution": dict(type_counts)}

def location_stats(records: list[WasteRecord]) -> list[dict]:
    groups = defaultdict(list)
    for r in records: groups[r.location].append(r)
    return [{"location": loc, **summarize(groups[loc])} for loc in CAMPUS_LOCATIONS]

def trend_stats(records: list[WasteRecord], days: int = 30, start: date | None = None, end: date | None = None) -> list[dict]:
    counts = Counter(r.created_at.date().isoformat() for r in records if r.created_at)
    last_day = end or date.today()
    first_day = start or last_day - timedelta(days=days - 1)
    span = (last_day - first_day).days
    return [{"date": (first_day + timedelta(days=i)).isoformat(), "records": counts[(first_day + timedelta(days=i)).isoformat()]}
            for i in range(max(0, span) + 1)]
