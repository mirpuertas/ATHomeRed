"""
Alembic environment configuration
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.infra.persistence.database import DATABASE_URL
from app.infra.persistence.base import Base

# Import all ORM models so Alembic can detect them
from app.infra.persistence import (  # noqa: F401
    usuarios,
    perfiles,
    paciente,
    ubicacion,
    servicios,
    agenda,
    valoraciones,
    matriculas,
    publicaciones,
    relaciones,
    auth,
)

config = context.config

# Override sqlalchemy.url with our DATABASE_URL
# Escapar % en la URL para evitar problemas con interpolacion de .ini
database_url_escaped = DATABASE_URL.replace("%", "%%")
config.set_main_option("sqlalchemy.url", database_url_escaped)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Include only athome schema
        include_schemas=True,
        include_object=lambda obj, name, type_, reflected, compare_to: (
            obj.schema == "athome" if hasattr(obj, "schema") else True
        ),
        version_table_schema=(
            target_metadata.schema if target_metadata.schema else None
        ),
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Include only athome schema
            include_schemas=True,
            include_object=lambda obj, name, type_, reflected, compare_to: (
                obj.schema == "athome" if hasattr(obj, "schema") else True
            ),
            version_table_schema=(
                target_metadata.schema if target_metadata.schema else None
            ),
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
