from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, func
from gov_monitor.database import Base


class NormalizedMetric(Base):
    __tablename__ = "normalized_metrics"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    district = Column(String(100), index=True)
    metric_category = Column(String(50))  # Environment, Economy, Utilities, Infrastructure, Health
    metric_name = Column(String(100))      # AQI, Mandi_Price, Reservoir_Level, Ev_Registrations, Active_Beds
    metric_value = Column(Float)
    unit = Column(String(20))
    confidence_score = Column(Float)       # Granular evaluation mapped row-by-row
    raw_payload = Column(JSON)


class ExecutiveSummary(Base):
    __tablename__ = "executive_summaries"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    district = Column(String(100))
    language = Column(String(20))
    summary_text = Column(Text)
