"""Database connection management using a Singleton pattern."""
from __future__ import annotations

from threading import Lock
import mysql.connector
from mysql.connector import Error

from config import settings


class DatabaseConnection:
    """Singleton factory for MySQL connections.

    A new physical connection is returned for each operation, while the class
    itself is instantiated only once. This keeps configuration centralized and
    makes the dependency easy to test/mock.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self, database: str | None = None):
        from config import get_ssl_ca_path

        connection_args = {
            "host": settings.host,
            "port": settings.port,
            "user": settings.user,
            "password": settings.password,
            "database": database,
            "autocommit": False,
        }

        ssl_ca_path = get_ssl_ca_path()

        if ssl_ca_path:
            connection_args.update(
                {
                    "ssl_ca": ssl_ca_path,
                    "ssl_verify_cert": settings.ssl_verify_cert,
                    "ssl_verify_identity": settings.ssl_verify_identity,
                }
            )

        return mysql.connector.connect(**connection_args)

    def test_connection(self, database: str | None = None) -> tuple[bool, str]:
        conn = None
        try:
            conn = self.connect(database)
            return True, "Database connection successful."
        except Error as exc:
            return False, f"Database connection failed: {exc}"
        finally:
            if conn and conn.is_connected():
                conn.close()
