import logging
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool, text

from project_template.api.common.database.models import (
    BaseEntity,
)  # noqa pycharm do not see it
from project_template.api.v1.imports import *  # noqa ruff does not like it
from project_template.config import DATABASE_SCHEMA, Env, settings
from project_template.logger import configure_logging

config = context.config
configure_logging()


logger = logging.getLogger("alembic")
target_metadata = BaseEntity.metadata


def process_revision_directives(_context, _revision, directives):
    """Assign sequential zero-padded numeric revision IDs (0013, 0014, …).


    This keeps migration filenames human-readable and sortable.
    """
    if not directives:
        return

    script = directives[0]
    versions_dir = Path(__file__).parent / "versions"

    max_seq = 0
    for f in versions_dir.glob("*.py"):
        prefix = f.stem.split("_", 1)[0]
        if prefix.isdigit():
            max_seq = max(max_seq, int(prefix))

    script.rev_id = f"{max_seq + 1:04d}"


def drop_alembic_version_if_dev(connection) -> None:
    """Drop the alembic_version table on DEV so revisions mismatch doesn't cause issues when running migrations."""
    logger.info("Current environment: %s", settings.environment)
    if settings.environment == Env.DEV:
        logger.info("Dropping alembic_version table")
        connection.execute(text(f"DROP SCHEMA IF EXISTS {DATABASE_SCHEMA} CASCADE;"))
        connection.execute(text("DROP TABLE IF EXISTS public.alembic_version"))
        logger.info("Dropped schema project_template and alembic_version table.")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.


    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.


    Calls to context.execute() here emit the given string to the
    script output.


    """
    context.configure(
        url=settings.database_connection_string.replace("asyncpg", "psycopg"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        process_revision_directives=process_revision_directives,
        version_table_schema=DATABASE_SCHEMA,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.


    In this scenario we need to create an Engine
    and associate a connection with the context.


    """
    connectable = config.attributes.get("connection", None)
    logger.info("Running online migrations")

    if not connectable:
        logger.info(
            "No connection found in config attributes, creating engine from config"
        )
        # Get the connection string and set it in the config
        configuration = config.get_section(config.config_ini_section, {})
        configuration["sqlalchemy.url"] = settings.database_connection_string.replace(
            "asyncpg", "psycopg"
        )

        connectable = engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        with connectable.connect() as connection:
            logger.info("Running migrations")
            _configure_and_run(connection)
    else:
        logger.info("Using existing connection from config attributes")
        _configure_and_run(connectable)


def _create_schema_if_not_exists(connection) -> None:
    if connection.in_transaction():
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {DATABASE_SCHEMA}"))
    else:
        with connection.begin():
            connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {DATABASE_SCHEMA}"))


def _configure_and_run(connection) -> None:
    # drop_alembic_version_if_dev(connection)
    _create_schema_if_not_exists(connection)

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        process_revision_directives=process_revision_directives,
        version_table_schema=DATABASE_SCHEMA,
    )

    with context.begin_transaction():
        logger.info("Running migrations")
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
