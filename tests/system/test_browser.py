import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.system


def test_full_task_lifecycle(page, live_url):
    page.goto(live_url)
    expect(page.get_by_role("heading", name="Здесь пока нет задач")).to_be_visible()
    page.get_by_label("Новая задача").fill("Подготовить проект")
    page.get_by_role("button", name="+ Добавить").click()
    expect(page.get_by_test_id("task")).to_have_count(1)
    page.reload()
    expect(page.get_by_test_id("task")).to_contain_text("Подготовить проект")
    page.get_by_role("link", name="Изменить: Подготовить проект").click()
    page.get_by_label("Название задачи").fill("Защитить проект")
    page.get_by_role("button", name="Сохранить").click()
    page.get_by_role("button", name="Завершить: Защитить проект").click()
    page.get_by_role("link", name="В работе", exact=True).click()
    expect(page.get_by_test_id("task")).to_have_count(0)
    page.get_by_role("link", name="Выполнено", exact=True).click()
    expect(page.get_by_test_id("task")).to_contain_text("Защитить проект")
    page.get_by_role("button", name="Вернуть в работу: Защитить проект").click()
    expect(page.get_by_role("button", name="Завершить: Защитить проект")).to_be_visible()
    page.get_by_role("button", name="Удалить: Защитить проект").click()
    expect(page.get_by_test_id("task")).to_have_count(0)
    page.reload()
    expect(page.get_by_role("heading", name="Здесь пока нет задач")).to_be_visible()


def test_whitespace_validation(page, live_url):
    page.goto(live_url)
    page.get_by_label("Новая задача").fill("   ")
    page.get_by_role("button", name="+ Добавить").click()
    expect(page.get_by_role("status")).to_contain_text("Введите название")
    expect(page.get_by_test_id("task")).to_have_count(0)


def test_mobile_layout(page, live_url):
    page.set_viewport_size({"width": 390, "height": 844})
    page.goto(live_url)
    page.get_by_label("Новая задача").fill("Мобильная задача " + "я" * 90)
    page.get_by_role("button", name="+ Добавить").click()
    expect(page.get_by_test_id("task")).to_be_visible()
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    page.get_by_role("button", name="Удалить:", exact=False).click()
    expect(page.get_by_test_id("task")).to_have_count(0)


def test_edit_cancel_and_not_found(page, live_url):
    page.goto(live_url)
    page.get_by_label("Новая задача").fill("Исходная")
    page.get_by_role("button", name="+ Добавить").click()
    page.get_by_role("link", name="Изменить: Исходная").click()
    page.get_by_label("Название задачи").fill("Не сохранять")
    page.get_by_role("link", name="Отмена").click()
    expect(page.get_by_test_id("task")).to_contain_text("Исходная")
    response = page.goto(live_url + "/tasks/999/edit")
    assert response.status == 404
    page.get_by_role("link", name="К списку задач").click()
    expect(page.get_by_test_id("task")).to_contain_text("Исходная")
