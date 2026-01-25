import sys
from pathlib import Path

# Add project root to PYTHONPATH
ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT_DIR))


from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from alembic import context
import asyncio

from app.persistence.base import Base
from app.config import settings


# IMPORTANT: import all models so Alembic sees them
from app.persistence.models.user import User
from app.persistence.models.birth_profile import BirthProfile
from app.persistence.models.kundali_core import KundaliCore
from app.persistence.models.kundali_derived import KundaliDerived
from app.persistence.models.kundali_divisional import KundaliDivisional
from app.persistence.models.rule import Rule
from app.persistence.models.rule_mapping import RuleMapping
from app.persistence.models.subscription import Subscription
from app.persistence.models.usage_log import UsageLog
from app.persistence.models.transit import Transit
from app.persistence.models.knowledge_item import KnowledgeItem
from app.persistence.models.chat_history import ChatHistory
from app.persistence.models.kundali_match import KundaliMatch




config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online():
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(
        settings.DATABASE_URL,
        poolclass=pool.NullPool,
    )

    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
