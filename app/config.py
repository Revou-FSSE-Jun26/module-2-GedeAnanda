import os
from datetime import timedelta
from urllib.parse import urlsplit

from dotenv import load_dotenv
from sqlalchemy.pool import NullPool

load_dotenv()

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", ""}


def _normalize_db_url(var_name):
    db_url = os.environ.get(var_name, "")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    return db_url


def _engine_options(db_url):
    """Engine settings tuned for serverless (one short-lived process per request).

    A pool is useless when the process dies after the response, and holding
    connections open exhausts the Postgres connection limit, so we use NullPool
    and let Supabase's transaction pooler (port 6543) do the pooling. That
    pooler also rejects server-side prepared statements, which psycopg2 does
    not emit on its own -- nothing to disable, but do not swap in a driver that
    does (psycopg3, asyncpg) without turning them off first.

    TLS is required for any remote host but skipped locally, where the dev
    server has no certificate.
    """
    options = {"poolclass": NullPool}
    host = urlsplit(db_url).hostname or ""
    if host not in LOCAL_HOSTS:
        options["connect_args"] = {"sslmode": "require", "connect_timeout": 10}
    return options


def _cors_origins():
    raw = os.environ.get("CORS_ORIGINS", "*")
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


class Config:
    SQLALCHEMY_DATABASE_URI = _normalize_db_url('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = _engine_options(SQLALCHEMY_DATABASE_URI)
    SECRET_KEY = os.environ.get('SECRET_KEY')

    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    CORS_ORIGINS = _cors_origins()


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = _normalize_db_url('TEST_DATABASE_URL')
    SQLALCHEMY_ENGINE_OPTIONS = _engine_options(SQLALCHEMY_DATABASE_URI)
