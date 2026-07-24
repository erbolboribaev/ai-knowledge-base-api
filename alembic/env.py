import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Loyiha ildizini import yo'liga qo'shish
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.db.base import Base
from app.models import User, Document, Chunk  # noqa: F401 - metadata'ga ro'yxatdan o'tishi uchun

# Alembic Config obyekti - alembic.ini'dagi qiymatlarga kirish imkonini beradi
config = context.config

# .env'dan olingan haqiqiy DATABASE_URL bilan almashtiramiz.
# asyncpg drayverini alembic (sync) bilan ishlatib bo'lmaydi,
# shuning uchun "+asyncpg"ni olib tashlaymiz - oddiy psycopg bilan ishlaydi.
sync_db_url = settings.database_url.replace("+asyncpg", "")
config.set_main_option("sqlalchemy.url", sync_db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Autogenerate uchun modellarimiz metadata'si
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
