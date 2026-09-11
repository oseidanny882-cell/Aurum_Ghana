"""
Alembic migration environment
"""
import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import config as app_config
from backend.extensions import db
from backend.models import *  # noqa: F401,F403

# The real alembic.ini lives at the project root, not inside migrations/
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ALEMBIC_INI = os.path.join(_ROOT, "alembic.ini")

config = context.config

if os.path.exists(_ALEMBIC_INI):
    config.config_file_name = _ALEMBIC_INI
    if os.path.exists(_ALEMBIC_INI):
        fileConfig(_ALEMBIC_INI)

target_metadata = db.metadata


def get_url():
    return app_config[os.getenv("FLASK_ENV", "development")].SQLALCHEMY_DATABASE_URI


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True,
                      dialect_opts={"paramstyle": "named"}, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(configuration, prefix="sqlalchemy.",
                                     poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata,
                          compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
