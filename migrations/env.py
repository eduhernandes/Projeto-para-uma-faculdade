from logging.config import fileConfig
from pathlib import Path

from alembic import context
from flask import current_app

config = context.config
if config.config_file_name is not None:
    config_path = Path(config.config_file_name)
    if not config_path.is_file():
        config_path = Path(__file__).resolve().parents[1] / "alembic.ini"
    fileConfig(config_path)

target_db = current_app.extensions["migrate"].db
target_metadata = target_db.metadata


def get_engine():
    return target_db.engine


def get_engine_url():
    return str(get_engine().url).replace('%', '%%')


def run_migrations_offline():
    context.configure(url=get_engine_url(), target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"}, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = get_engine()
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True if connectable.url.drivername.startswith('sqlite') else False, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
