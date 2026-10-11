import re
import sqlite3

import pytest

from app import create_app
from app.db import close_db, get_db, init_db

pytestmark = pytest.mark.integration


def test_empty_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Добавьте первое дело" in response.text


def test_create_trims_title(client, app):
    response = client.post("/tasks", data={"title": "  Учить Flask  "}, follow_redirects=True)
    assert "Учить Flask" in response.text
    with app.app_context():
        row = get_db().execute("SELECT * FROM tasks").fetchone()
        assert row["title"] == "Учить Flask"
        assert row["done"] == 0


@pytest.mark.parametrize("title", ["", "   ", "x" * 121])
def test_invalid_create(client, app, title):
    response = client.post("/tasks", data={"title": title}, follow_redirects=True)
    assert 'class="notice error"' in response.text
    with app.app_context():
        assert get_db().execute("SELECT COUNT(*) FROM tasks").fetchone()[0] == 0


def test_missing_title(client):
    assert "Введите название" in client.post("/tasks", follow_redirects=True).text


def test_edit(client, app):
    client.post("/tasks", data={"title": "До"})
    assert 'value="До"' in client.get("/tasks/1/edit").text
    response = client.post("/tasks/1/edit", data={"title": " После "}, follow_redirects=True)
    assert "После" in response.text
    with app.app_context():
        assert get_db().execute("SELECT title FROM tasks").fetchone()[0] == "После"


@pytest.mark.parametrize("title", [" ", "a" * 121])
def test_invalid_edit_keeps_old_title(client, app, title):
    client.post("/tasks", data={"title": "Исходное название"})
    response = client.post("/tasks/1/edit", data={"title": title})
    assert response.status_code == 400
    with app.app_context():
        assert get_db().execute("SELECT title FROM tasks").fetchone()[0] == "Исходное название"


def test_toggle_twice(client, app):
    client.post("/tasks", data={"title": "Сделать"})
    for expected in (1, 0):
        assert client.post("/tasks/1/toggle").status_code == 302
        with app.app_context():
            assert get_db().execute("SELECT done FROM tasks").fetchone()[0] == expected


def test_filters_and_counts(client):
    client.post("/tasks", data={"title": "Активная задача"})
    client.post("/tasks", data={"title": "Готовая задача"})
    client.post("/tasks/2/toggle")
    active = client.get("/?status=active").text
    done = client.get("/?status=done").text
    assert "Активная задача" in active and "Готовая задача" not in active
    assert "Готовая задача" in done and "Активная задача" not in done
    page = client.get("/?status=unknown").text
    assert "Активная задача" in page and "Готовая задача" in page
    assert "<strong>2</strong>" in page
    assert page.count("<strong>1</strong>") == 2


def test_newest_first(client):
    for title in ("Первая", "Вторая"):
        client.post("/tasks", data={"title": title})
    page = client.get("/").text
    assert page.index('class="task-title">Вторая') < page.index('class="task-title">Первая')


def test_delete_only_selected_task(client, app):
    for title in ("Удалить", "Оставить"):
        client.post("/tasks", data={"title": title})
    assert client.post("/tasks/1/delete").status_code == 302
    with app.app_context():
        rows = get_db().execute("SELECT title FROM tasks").fetchall()
        assert [row[0] for row in rows] == ["Оставить"]


@pytest.mark.parametrize(
    "path, method",
    [
        ("/missing", "get"),
        ("/tasks/999/edit", "get"),
        ("/tasks/999/edit", "post"),
        ("/tasks/999/toggle", "post"),
        ("/tasks/999/delete", "post"),
    ],
)
def test_not_found(client, path, method):
    response = getattr(client, method)(path)
    assert response.status_code == 404
    assert "не найдена" in response.text


@pytest.mark.parametrize("path", ["/tasks", "/tasks/1/delete", "/tasks/1/toggle"])
def test_mutations_require_post(client, path):
    assert client.get(path).status_code == 405


def test_html_is_escaped(client):
    client.post("/tasks", data={"title": "<script>alert(1)</script>"})
    page = client.get("/").text
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page


def test_sql_text_is_data(client):
    title = "'); DROP TABLE tasks; --"
    client.post("/tasks", data={"title": title})
    client.post("/tasks", data={"title": "База работает"})
    assert "База работает" in client.get("/").text


def test_persistence_after_restart(app, client):
    client.post("/tasks", data={"title": "Сохранённая задача"})
    restarted = create_app(dict(app.config))
    assert "Сохранённая задача" in restarted.test_client().get("/").text


def test_connections_close_and_schema_is_idempotent(app):
    with app.app_context():
        connection = get_db()
        assert get_db() is connection
        init_db()
        close_db()
        close_db()
        with pytest.raises(sqlite3.ProgrammingError):
            connection.execute("SELECT 1")
        assert get_db() is not connection


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_request_size_limit(client):
    assert client.post("/tasks", data={"title": "x" * 20000}).status_code == 413


def test_csrf_protection(app):
    app.config["WTF_CSRF_ENABLED"] = True
    browser = app.test_client()
    assert browser.post("/tasks", data={"title": "Без токена"}).status_code == 400
    assert (
        browser.post("/tasks", data={"title": "Неверный", "csrf_token": "bad"}).status_code == 400
    )
    page = browser.get("/").text
    token = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)
    assert (
        browser.post("/tasks", data={"title": "С токеном", "csrf_token": token}).status_code == 302
    )


def test_default_configuration_uses_environment(tmp_path, monkeypatch):
    database = str(tmp_path / "nested" / "environment.sqlite")
    monkeypatch.setenv("DATABASE", database)
    monkeypatch.setenv("SECRET_KEY", "environment-secret")
    application = create_app()
    assert application.config["DATABASE"] == database
    assert application.config["SECRET_KEY"] == "environment-secret"
    assert application.test_client().get("/health").status_code == 200
