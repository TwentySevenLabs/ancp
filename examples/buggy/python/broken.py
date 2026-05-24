import does_not_exist
from math import missing_name


def add(a: int, b: int) -> str:
    return a + b


def call_missing() -> None:
    render_user({"name": "Ada"})
    print(undefined_value)


def syntax_error():
    if True
        print("missing colon above")

