
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, CheckConstraint, Index, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'waste_management.db')}")
if DATABASE_URL.startswith("postgres://"):
    # Some managed PostgreSQL providers still supply this legacy URL scheme.
    DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]

engine_options = {"pool_pre_ping": True}
if make_url(DATABASE_URL).get_backend_name() == "sqlite":
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_options)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


class WasteRecord(Base):
    __tablename__ = "waste_records"
    __table_args__ = (
        CheckConstraint("confidence >= 0 AND confidence <= 100", name="ck_record_confidence"),
        CheckConstraint("weight_kg IS NULL OR weight_kg >= 0", name="ck_record_weight"),
        Index("ix_waste_records_created_at", "created_at"),
        Index("ix_waste_records_location_category", "location", "waste_category"),
    )

    id = Column(Integer, primary_key=True, index=True)
    waste_category = Column(String, nullable=False)
    waste_type = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    location = Column(String, nullable=False)
    selected_bin = Column(String, nullable=True)
    is_correctly_segregated = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    image_filename = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    weight_kg = Column(Float, nullable=True)


def create_tables():
    Base.metadata.create_all(bind=engine)
    # Preserve older local databases and add optional fields to older deployments.
    with engine.begin() as connection:
        optional_columns = (("image_filename", "VARCHAR"), ("notes", "VARCHAR"), ("weight_kg", "FLOAT"))
        if connection.dialect.name == "sqlite":
            existing = {row[1] for row in connection.execute(text("PRAGMA table_info(waste_records)"))}
            for name, sql_type in optional_columns:
                if name not in existing:
                    connection.execute(text(f"ALTER TABLE waste_records ADD COLUMN {name} {sql_type}"))
        elif connection.dialect.name == "postgresql":
            for name, sql_type in optional_columns:
                connection.execute(text(
                    f"ALTER TABLE waste_records ADD COLUMN IF NOT EXISTS {name} {sql_type}"
                ))
    Index("ix_waste_records_created_at", WasteRecord.created_at).create(bind=engine, checkfirst=True)
    Index("ix_waste_records_location_category", WasteRecord.location, WasteRecord.waste_category).create(bind=engine, checkfirst=True)
