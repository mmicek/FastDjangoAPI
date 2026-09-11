from contextlib import asynccontextmanager

import pytest
from starlette.testclient import TestClient

from project_template.config import Env, settings
from project_template.main import TemplateApp, create_app


@pytest.fixture()
async def app(_test_database_manager, context_db):

    @asynccontextmanager
    async def lifespan(_):
        yield

    settings.ENV = Env.TEST
    app = create_app(life_span=lifespan)
    app.session_manager = _test_database_manager
    yield app


@pytest.fixture(scope="function")
def client(app: TemplateApp):
    with TestClient(app) as client:
        yield client
