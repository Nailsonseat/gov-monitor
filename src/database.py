from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from gov_monitor.config import Config

engine = create_engine(
    Config.DATABASE_URL,
    connect_args={"application_name": "gov_monitor_pipeline"}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    import gov_monitor.schemas.models
    Base.metadata.create_all(bind=engine)
