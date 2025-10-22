from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

import sys, pathlib, os

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from core.settings import settings          # lê .env (DB_URL, etc.)
from models.models import Base                     # seu DeclarativeBase
from models.models_rbac import *



# Config do Alembic
config = context.config

# Opcional: escrever a URL no ini via code:
config.set_main_option("sqlalchemy.url", settings.DB_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Rodar sem conexão (gera SQL)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,   # detecta mudança de tipo
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Rodar com conexão real."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
