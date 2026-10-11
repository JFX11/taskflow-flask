"""Чистые функции: не зависят от Flask или базы данных."""

MAX_TITLE_LENGTH = 120
FILTERS = ("all", "active", "done")


def validate_title(value):
    title = value.strip()
    if not title:
        raise ValueError("Введите название задачи.")
    if len(title) > MAX_TITLE_LENGTH:
        raise ValueError("Название не должно превышать 120 символов.")
    return title


def validate_filter(value):
    return value if value in FILTERS else "all"
