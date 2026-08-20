from pathlib import Path
from unittest import mock

import pytest
from alembic import command
from alembic.config import Config
from psycopg.errors import UndefinedTable
from sqlalchemy import String, create_engine, text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Mapped, Session, mapped_column

from project_template.api.common.database.models import BaseEntity
from project_template.config import DATABASE_SCHEMA
from project_template.tests.factories.database import create_instance_factory


@pytest.mark.asyncio()
def test_if_migrations_are_up_to_date(_test_database_manager):
    """
    Simple test that checks, if the newest migration is generated. It tests if after applying migrations,
    all tables, columns, relationships in the database are the same as in the code.
    """

    def _test_create_all_entities():
        with Session(bind=connection) as session:
            # Defer all constraints to be able to check if columns matches migrations to BaseEntity
            session.execute(text("SET session_replication_role = replica;"))
            session.execute(text("SET CONSTRAINTS ALL DEFERRED;"))

            for model_mapper in BaseEntity.registry.mappers:
                instance = create_instance_factory(
                    model_mapper.class_,
                    populate_random_foreign_keys=True,
                )
                session.add(instance)

            session.flush()
            session.commit()

    engine = create_engine(_test_database_manager.connection_string)
    with engine.connect() as connection:
        with connection.begin():
            connection.execute(
                text(f"DROP SCHEMA IF EXISTS {DATABASE_SCHEMA} CASCADE;")
            )
            connection.execute(text(f"CREATE SCHEMA {DATABASE_SCHEMA};"))

            with mock.patch(
                "sqlalchemy.engine.base.Engine.connect"
            ) as transaction_mock:
                transaction_mock.return_value.__enter__.return_value = connection

                current_dir = Path(__file__).parent
                alembic_ini_path = current_dir / "../../.." / "alembic.ini"
                alembic_dir_path = current_dir / "../.." / "alembic"

                alembic_cfg = Config(str(alembic_ini_path.resolve()))
                alembic_cfg.set_main_option(
                    "script_location", str(alembic_dir_path.resolve())
                )

                command.upgrade(alembic_cfg, "head")

                with connection.begin_nested() as transaction_nested:
                    # Rollback to have clean empty database to test downgrade
                    _test_create_all_entities()
                    transaction_nested.rollback()

                class _(BaseEntity):
                    __tablename__ = "dummy_entity"
                    value: Mapped[str | None] = mapped_column(String)

                try:
                    # This one should fail due to missing DummyEntity table migration.
                    # This tests if test is valid.
                    with connection.begin_nested():
                        # We need nested to not close outer transaction due to rollback
                        _test_create_all_entities()
                except ProgrammingError as e:
                    assert isinstance(e.orig, UndefinedTable)

                # Tests if downgrades are proper
                command.downgrade(alembic_cfg, "0001")

            connection.rollback()
