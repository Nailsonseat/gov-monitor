from google import genai
from sqlalchemy.orm import Session
from gov_monitor.config import Config
from gov_monitor.schemas.models import NormalizedMetric, ExecutiveSummary


def generate_llm_intelligence(db: Session):
    """
    Pulls recent metrics to feed the synthesis layer, writing out localized administrative updates.
    """
    recent_metrics = db.query(NormalizedMetric).order_by(NormalizedMetric.timestamp.desc()).limit(15).all()
    if not recent_metrics:
        return

    data_payload = ", ".join([f"{m.metric_name}: {m.metric_value} {m.unit}" for m in recent_metrics])
    client = genai.Client(api_key=Config.GEMINI_API_KEY)

    prompt = (
        f"You are an administrative AI assistant writing directly to the District Magistrate of {Config.TARGET_DISTRICT}. "
        f"Synthesize this regional dataset matrix: {data_payload}. "
        f"Generate a strict 3-sentence executive alert update covering environment, economic indicators, and public resources. "
        f"Your response must be entirely in natural, professional {Config.LANGUAGE_TARGET} script."
    )

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )

        summary = ExecutiveSummary(
            district=Config.TARGET_DISTRICT,
            language=Config.LANGUAGE_TARGET,
            summary_text=response.text
        )
        db.add(summary)
        db.commit()
    except Exception as e:
        print(f"Failed to compile AI executive summary: {e}")
