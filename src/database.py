from src.config import Config
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Intercept and generate the ca.pem file dynamically before connection
db_ca_cert = os.getenv("DB_CA_CERT")
if db_ca_cert:
    # Handles literal string escapes so the PEM file is formatted properly
    formatted_cert = db_ca_cert.replace("\\n", "\n")
    with open("ca.pem", "w") as f:
        f.write(formatted_cert)

engine = create_engine(
    Config.DATABASE_URL,
    connect_args={"application_name": "gov_monitor_pipeline"}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    import src.schemas.models
    Base.metadata.create_all(bind=engine)
