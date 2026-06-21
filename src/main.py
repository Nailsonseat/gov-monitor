import time
import threading
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from src.config import Config
from src.database import init_db, SessionLocal
from src.ingestion.signals import SIGNAL_EXTRACTORS
from src.pipeline.scoring import calculate_confidence
from src.schemas.models import NormalizedMetric
from src.pipeline.synthesizer import generate_llm_intelligence


def _format_metric_snapshot(metric: NormalizedMetric, field_issues: list[str]) -> str:
    """Build a structured stdout snapshot for a row entering CockroachDB."""
    issues_display = ", ".join(field_issues) if field_issues else "none"
    return (
        f"  district={metric.district} | category={metric.metric_category} | "
        f"metric={metric.metric_name} | value={metric.metric_value} {metric.unit} | "
        f"confidence={metric.confidence_score} | field_warnings=[{issues_display}]"
    )


def run_pipeline():
    """
    Execute one full ingestion → scoring → persistence → synthesis cycle.

    All stages emit verbose stdout logs so container terminals surface live
    ingestion state, normalized metrics, confidence scores, and LLM output.
    """
    print("[PIPELINE] Verifying database engine state and initialization...")
    init_db()

    db = SessionLocal()
    metrics_persisted = 0

    try:
        print(
            f"[PIPELINE] Cycle configuration: "
            f"fetch_interval={Config.API_FETCH_INTERVAL_SECONDS}s, "
            f"max_rows_per_call={Config.MAX_ROWS_PER_API_CALL}, "
            f"target_district={Config.TARGET_DISTRICT}"
        )

        for ExtractorClass in SIGNAL_EXTRACTORS:
            extractor = ExtractorClass()
            records = extractor.fetch_raw()

            print(
                f"[PIPELINE] Processing signal [{extractor.metric_name}]: "
                f"{len(records)} row(s) to normalize and score"
            )

            for record in records:
                value, field_issues = extractor.parse_with_audit(record)
                confidence = calculate_confidence(
                    value,
                    record,
                    extractor.metric_name,
                    field_issues=field_issues,
                )

                metric = NormalizedMetric(
                    district=Config.TARGET_DISTRICT,
                    metric_category=extractor.category,
                    metric_name=extractor.metric_name,
                    metric_value=value,
                    unit=extractor.unit,
                    confidence_score=confidence,
                    raw_payload=record,
                )
                db.add(metric)
                metrics_persisted += 1

                print("[PIPELINE] Normalized metric entering CockroachDB:")
                print(_format_metric_snapshot(metric, field_issues))

                if field_issues:
                    print(
                        f"[PIPELINE] Confidence penalty applied for "
                        f"[{extractor.metric_name}]: score={confidence}, "
                        f"issues={field_issues}"
                    )
                elif confidence < 1.0:
                    print(
                        f"[PIPELINE] Anomaly confidence adjustment for "
                        f"[{extractor.metric_name}]: score={confidence}"
                    )

        if metrics_persisted:
            db.commit()
            print(f"[PIPELINE] Committed {metrics_persisted} normalized metric row(s).")
        else:
            print("[PIPELINE] No metrics persisted this cycle.")

        generate_llm_intelligence(db)

    except Exception as e:
        db.rollback()
        print(f"[PIPELINE] CRITICAL: Cycle failed, transaction rolled back: {e}")
        raise
    finally:
        db.close()


class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Pipeline Daemon is Active")


def run_dummy_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    print(f"[PIPELINE] Health-check server listening on port {port}...")
    server.serve_forever()


if __name__ == "__main__":
    server_thread = threading.Thread(target=run_dummy_server, daemon=True)
    server_thread.start()

    print("[PIPELINE] Initiating continuous pipeline daemon...")
    while True:
        try:
            run_pipeline()
        except Exception as e:
            print(f"[PIPELINE] CRITICAL: Pipeline cycle failed: {e}")

        print(
            f"[PIPELINE] Cycle complete. Sleeping for "
            f"{Config.API_FETCH_INTERVAL_SECONDS} second(s)..."
        )
        time.sleep(Config.API_FETCH_INTERVAL_SECONDS)
