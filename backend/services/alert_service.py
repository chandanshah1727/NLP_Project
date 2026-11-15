"""Alerts derived from recorded segregation decisions."""
from collections import Counter
from datetime import datetime, timedelta, timezone
from backend.services.analytics_service import location_stats

def generate_alerts(records: list, threshold: float = 70.0) -> list[dict]:
    alerts = []
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    recent_start = now - timedelta(days=7)
    previous_start = now - timedelta(days=14)
    recent_incorrect = sum(r.is_correctly_segregated == 0 and r.created_at and r.created_at >= recent_start for r in records)
    previous_incorrect = sum(r.is_correctly_segregated == 0 and r.created_at and previous_start <= r.created_at < recent_start for r in records)
    if recent_incorrect > previous_incorrect:
        alerts.append({"severity": "high" if recent_incorrect >= 3 else "medium", "location": "All locations",
                       "type": "increasing_incorrect_records", "message": f"Incorrect segregation records increased from {previous_incorrect} in the prior 7 days to {recent_incorrect} in the latest 7 days.", "count": recent_incorrect})
    for row in location_stats(records):
        if row["total_records"] and row["compliance_percentage"] < threshold:
            alerts.append({"severity": "high" if row["compliance_percentage"] < 50 else "medium", "location": row["location"],
                           "type": "low_compliance", "message": f"{row['location']} segregation compliance is {row['compliance_percentage']:.1f}% (below {threshold:.0f}%).", "count": row["incorrect_records"]})
    incorrect = [r for r in records if r.is_correctly_segregated == 0]
    by_location = Counter(r.location for r in incorrect)
    for loc, count in by_location.items():
        if count >= 3:
            alerts.append({"severity": "medium", "location": loc, "type": "repeated_issues", "message": f"{count} incorrect segregation decisions have been recorded at {loc}.", "count": count})
    by_category = Counter(r.waste_category for r in incorrect)
    for category, count in by_category.items():
        if count >= 3:
            alerts.append({"severity": "low", "location": "All locations", "type": "category_attention", "message": f"{category.title()} has {count} incorrect segregation decisions; review local handling guidance.", "count": count})
    return alerts
