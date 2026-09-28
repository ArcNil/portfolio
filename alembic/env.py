"""Alembic migration environment.

The database URL is resolved at runtime from DATABASE_URL_ENDPOINT so
migrations always run against the current database.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from app.database import resolve_database_url
from app.forex_forecast.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Point Alembic at the database URL: fetched fresh from DATABASE_URL_ENDPOINT
# (the prod URL changes over time), falling back to DATABASE_URL if the
# endpoint is unreachable.
config.set_main_option("sqlalchemy.url", resolve_database_url())

# Model metadata for `alembic revision --autogenerate`.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Emit SQL to stdout without a live DB connection."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        dialect_name="postgresql",
        as_sql=True,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Connect to the database and apply migrations in place."""
    engine = create_engine(config.get_main_option("sqlalchemy.url"))
    with engine.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()