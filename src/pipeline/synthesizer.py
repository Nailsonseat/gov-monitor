from google import genai
from sqlalchemy.orm import Session
from src.config import Config
from src.schemas.models import NormalizedMetric, ExecutiveSummary

# Bilingual section headers enforced in LLM output and used for log parsing.
ENGLISH_HEADER = "=== ENGLISH SUMMARY ==="
MARATHI_HEADER = "=== मराठी सारांश ==="
BILINGUAL_LANGUAGE_TAG = "English+Marathi"


def generate_llm_intelligence(db: Session):
    """
    Pull recent metrics, synthesize a bilingual executive alert (English + Marathi),
    and persist the combined block without truncation.
    """
    recent_metrics = (
        db.query(NormalizedMetric)
        .order_by(NormalizedMetric.timestamp.desc())
        .limit(15)
        .all()
    )
    if not recent_metrics:
        print("[SYNTHESIZER] No recent metrics available; skipping LLM summary generation.")
        return

    data_payload = ", ".join(
        f"{m.metric_name}: {m.metric_value} {m.unit} (confidence={m.confidence_score})"
        for m in recent_metrics
    )

    print(f"[SYNTHESIZER] Feeding {len(recent_metrics)} metric(s) to Gemini for bilingual synthesis...")

    client = genai.Client(api_key=Config.GEMINI_API_KEY)

    prompt = (
        f"You are an administrative AI assistant writing directly to the District Magistrate of {Config.TARGET_DISTRICT}. "
        f"Synthesize this regional dataset matrix: {data_payload}. "
        f"Generate a strict 3-sentence executive alert update covering environment, economic indicators, and public resources. "
        f"Your response MUST contain exactly two sections with these exact headers on their own lines:\n"
        f"{ENGLISH_HEADER}\n"
        f"(3 sentences in professional English)\n"
        f"{MARATHI_HEADER}\n"
        f"(3 sentences in natural, professional Marathi script)\n"
        f"Do not add any other sections or preamble."
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )

        summary_text = response.text.strip()

        # Persist the full bilingual block; Text column has no practical length cap.
        summary = ExecutiveSummary(
            district=Config.TARGET_DISTRICT,
            language=BILINGUAL_LANGUAGE_TAG,
            summary_text=summary_text,
        )
        db.add(summary)
        db.commit()

        print("[SYNTHESIZER] Bilingual intelligence summary generated and stored:")
        print("-" * 60)
        print(summary_text)
        print("-" * 60)

    except Exception as e:
        print(f"[SYNTHESIZER] Failed to compile AI executive summary: {e}")
