import asyncio
import sys

from project_template.config import settings

if sys.platform == "win32":
    from asyncio import WindowsSelectorEventLoopPolicy

    asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())


settings.DATABASE_NAME = "database-test"
pytest_plugins = [
    "project_template.tests.fixtures.app",
    "project_template.tests.fixtures.database",
    "project_template.tests.fixtures.data",
]
