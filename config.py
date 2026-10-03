from __future__ import annotations

import os
import tempfile
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "3306"))
    user: str = os.getenv("DB_USER", "root")
    password: str = os.getenv("DB_PASSWORD", "")

    staging_db: str = os.getenv("STAGING_DB", "employee_staging")
    oltp_db: str = os.getenv("OLTP_DB", "employee_oltp")
    olap_db: str = os.getenv("OLAP_DB", "employee_dw")

    ssl_ca: str = os.getenv("DB_SSL_CA", "")
    ssl_ca_content: str = os.getenv("DB_SSL_CA_CONTENT", "")

    ssl_verify_cert: bool = (
        os.getenv("DB_SSL_VERIFY_CERT", "false").lower() == "true"
    )

    ssl_verify_identity: bool = (
        os.getenv("DB_SSL_VERIFY_IDENTITY", "false").lower() == "true"
    )


settings = Settings()


def get_ssl_ca_path() -> str:
    """
    Return the CA certificate path.

    Local development:
        Uses DB_SSL_CA, e.g. certs/aiven-ca.pem

    Streamlit Cloud:
        Uses DB_SSL_CA_CONTENT from secrets and creates
        a temporary CA certificate file.
    """

    # Local certificate file
    if settings.ssl_ca and Path(settings.ssl_ca).exists():
        return settings.ssl_ca

    # Cloud certificate stored as a secret
    if settings.ssl_ca_content:
        ca_path = Path(tempfile.gettempdir()) / "aiven-ca.pem"

        ca_path.write_text(
            settings.ssl_ca_content,
            encoding="utf-8"
        )

        return str(ca_path)

    return ""