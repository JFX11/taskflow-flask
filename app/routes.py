"""Маршруты: читаем форму, проверяем данные, выполняем SQL, показываем страницу."""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from .db import get_db
from .validation import validate_filter, validate_title

bp = Blueprint("tasks", __name__)


def get_task(task_id):
    task = get_db().execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if task is None:
        abort(404)
    return task


@bp.get("/")
def index():
    status = validate_filter(request.args.get("status", "all"))
    database = get_db()
    if status == "all":
        tasks = database.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
    else:
        tasks = database.execute(
            "SELECT * FROM tasks WHERE done = ? ORDER BY id DESC", (int(status == "done"),)
        ).fetchall()
    counts = database.execute(
        "SELECT COUNT(*) AS total, COALESCE(SUM(done), 0) AS done FROM tasks"
    ).fetchone()
    return render_template("index.html", tasks=tasks, status=status, counts=counts)


@bp.post("/tasks")
def create():
    try:
        title = validate_title(request.form.get("title", ""))
    except ValueError as error:
        flash(str(error), "error")
        return redirect(url_for("tasks.index"))
    database = get_db()
    database.execute("INSERT INTO tasks (title) VALUES (?)", (title,))
    database.commit()
    flash("Задача добавлена.", "success")
    return redirect(url_for("tasks.index"))


@bp.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
def edit(task_id):
    task = get_task(task_id)
    if request.method == "POST":
        try:
            title = validate_title(request.form.get("title", ""))
        except ValueError as error:
            return render_template("edit.html", task=task, error=str(error)), 400
        database = get_db()
        database.execute("UPDATE tasks SET title = ? WHERE id = ?", (title, task_id))
        database.commit()
        flash("Задача обновлена.", "success")
        return redirect(url_for("tasks.index"))
    return render_template("edit.html", task=task)


@bp.post("/tasks/<int:task_id>/toggle")
def toggle(task_id):
    get_task(task_id)
    database = get_db()
    database.execute("UPDATE tasks SET done = 1 - done WHERE id = ?", (task_id,))
    database.commit()
    return redirect(url_for("tasks.index"))


@bp.post("/tasks/<int:task_id>/delete")
def delete(task_id):
    get_task(task_id)
    database = get_db()
    database.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    database.commit()
    flash("Задача удалена.", "success")
    return redirect(url_for("tasks.index"))


@bp.get("/health")
def health():
    get_db().execute("SELECT 1").fetchone()
    return {"status": "ok"}


@bp.app_errorhandler(404)
def not_found(error):
    return render_template("error.html", message="Эта страница или задача не найдена."), 404
