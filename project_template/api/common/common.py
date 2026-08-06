from typing import Any


def convert_to_boolean(value: Any):
    if isinstance(value, str):
        if value.lower() == "true" or value == "1":
            return True
        elif value.lower() == "false" or value == "0":
            return False
    return bool(value)
