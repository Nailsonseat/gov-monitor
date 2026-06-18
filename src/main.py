from src.database import init_db, SessionLocal
from src.ingestion.signals import SIGNAL_EXTRACTORS
from src.pipeline.scoring import calculate_confidence
from src.schemas.models import NormalizedMetric
from src.pipeline.synthesizer import generate_llm_intelligence


def run_pipeline():
    print("Verifying Database Engine State & Initialization...")
    init_db()

    db = SessionLocal()
    try:
        print("Engaging Consolidated Processing Task...")
        for ExtractorClass in SIGNAL_EXTRACTORS:
            extractor = ExtractorClass()
            records = extractor.fetch_raw()

            print(f"Processing signal matrix: {extractor.metric_name} | Rows Found: {len(records)}")
            for r in records:
                try:
                    val = extractor.parse_value(r)
                    confidence = calculate_confidence(val, r, extractor.metric_name)

                    metric = NormalizedMetric(
                        district=r.get("district", "Unknown"),
                        metric_category=extractor.category,
                        metric_name=extractor.metric_name,
                        metric_value=val,
                        unit=extractor.unit,
                        confidence_score=confidence,
                        raw_payload=r
                    )
                    db.add(metric)
                except Exception as row_error:
                    print(f"Filtering dirty/unparseable telemetry record row: {row_error}")
            db.commit()

        print("Triggering Multi-Signal Intelligence Aggregation...")
        generate_llm_intelligence(db)
        print("Data Extraction Cycle Successfully Formatted.")

    finally:
        db.close()


if __name__ == "__main__":
    run_pipeline()
