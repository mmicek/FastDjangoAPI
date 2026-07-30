import logging
from typing import Type

from project_template.api.common.exceptions.exceptions import ApiBaseException


def assert_status(
    response,
    status_code: int = 200,
    expected_message=None,
    expected_response_body: dict = None,
):
    """Asserts that an HTTP response matches the expected status code."""
    assert response.status_code == status_code, response.json()
    if expected_message:
        assert response.json()["message"] == expected_message
    if expected_response_body:
        assert response.json() == expected_response_body
    return True


def assert_exception(
    response,
    expected_exception_class: Type[ApiBaseException],
    expected_message: str = None,
    expected_details: dict = None,
):
    """Asserts that an HTTP response matches the expected exception type and message."""
    assert response.status_code == expected_exception_class.status_code
    response_json = response.json()
    assert response_json["error_code"] == expected_exception_class.error_code
    assert response_json["message"] == (
        expected_message or expected_exception_class.default_message
    )
    if expected_details is not None:
        assert response_json["details"] == expected_details


def assert_lists_equal_any_order(list1, list2):
    """Compares two lists for equality without considering order."""
    assert sorted(list1) == sorted(list2)


def assert_dicts_equal(dict1: dict, dict2: dict):
    """Compares two dictionaries for equality."""
    try:
        assert dict1 == dict2
    except AssertionError as e:
        logging.error(f"Dictionaries do not match: {dict1} != {dict2}")
        raise AssertionError(f"Dictionaries do not match: {dict1} != {dict2}") from e
