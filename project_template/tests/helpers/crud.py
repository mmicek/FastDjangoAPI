from starlette.testclient import TestClient

from project_template.api.common.database.models import BaseEntity
from project_template.api.common.views import (
    CreateMixin,
    DestroyMixin,
    GenericViewSet,
    ListMixin,
    RetrieveMixin,
    UpdateMixin,
)
from project_template.tests.factories.database import get_body_from_entity
from project_template.tests.helpers.assertions import assert_status


def crud_view_set_test(
    client: TestClient,
    entity: BaseEntity,
    base_url: str,
    view_set: type[GenericViewSet],
):
    """
    Basic test for CRUD view set. Tests if ViewSet is properly configured
    with Filters and Serializers.
    """
    assert view_set.model is type(
        entity
    ), "Object 'entity' should be the same type as the model type of the view set."

    view_set_actions = []
    for mixin in [ListMixin, RetrieveMixin, CreateMixin, UpdateMixin, DestroyMixin]:
        if issubclass(view_set, mixin):
            view_set_actions.append(mixin)

    url = base_url + view_set.url_prefix

    if ListMixin in view_set_actions:
        response = client.get(url)
        assert_status(response)
        assert len(response.json()) == 1
        data = response.json()[0]
        assert data["id"] == entity.id

    if RetrieveMixin in view_set_actions:
        response = client.get(url + f"/{entity.id}")
        assert_status(response)
        data = response.json()
        assert data["id"] == entity.id

    if UpdateMixin in view_set_actions:
        response = client.patch(url + f"/{entity.id}", json={})
        assert_status(response)

    if CreateMixin in view_set_actions:
        body = get_body_from_entity(entity)
        if "id" in body:
            del body["id"]
        response = client.post(url, json=body)
        assert_status(response)

    if DestroyMixin in view_set_actions:
        response = client.delete(url + f"/{entity.id}")
        assert_status(response)
