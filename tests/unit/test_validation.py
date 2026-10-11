import pytest

from app.validation import validate_filter, validate_title

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("Задача", "Задача"),
        ("  План  ", "План"),
        ("\nОтчёт\t", "Отчёт"),
        ("a" * 120, "a" * 120),
        ("Прочитать 📚", "Прочитать 📚"),
    ],
)
def test_valid_title(raw, expected):
    assert validate_title(raw) == expected


@pytest.mark.parametrize("raw", ["", " ", "\n\t", "a" * 121])
def test_invalid_title(raw):
    with pytest.raises(ValueError):
        validate_title(raw)


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("all", "all"),
        ("active", "active"),
        ("done", "done"),
        ("unknown", "all"),
        ("", "all"),
        ("DONE", "all"),
    ],
)
def test_filters(raw, expected):
    assert validate_filter(raw) == expected
