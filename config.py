import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import OperationalError

load_dotenv()


def build_database_uri() -> str:
    """Use DATABASE_URL if set, otherwise build a MySQL URL from DB_* variables."""
    explicit = os.getenv("DATABASE_URL")
    if explicit:
        return explicit
    url = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME", "ems_db"),
        query={"charset": "utf8mb4"},
    )
    return url.render_as_string(hide_password=False)


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-change-me")
    SQLALCHEMY_DATABASE_URI = build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")


def ensure_database(uri: str) -> None:
    """Create the MySQL database if it does not exist yet (no-op for other databases)."""
    url = make_url(uri)
    if not url.drivername.startswith("mysql"):
        return
    # URL.set(database=None) keeps the old database, so build a URL without one
    server_url = URL.create(
        drivername=url.drivername,
        username=url.username,
        password=url.password,
        host=url.host,
        port=url.port,
        query=url.query,
    )
    engine = create_engine(server_url)
    try:
        with engine.connect() as conn:
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{url.database}` "
                              "CHARACTER SET utf8mb4"))
            conn.commit()
    except OperationalError as exc:
        raise SystemExit(
            "\nCould not connect to MySQL. Check that:\n"
            "  1. MySQL server is running\n"
            "  2. DB_USER / DB_PASSWORD / DB_HOST / DB_PORT in your .env file are correct\n"
            f"\nOriginal error: {exc.orig}\n"
        ) from exc
    finally:
        engine.dispose()