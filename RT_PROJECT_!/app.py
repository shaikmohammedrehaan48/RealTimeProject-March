from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "expenses.db"
DEFAULT_MONTHLY_BUDGET = 5000.0

app = Flask(__name__)


def get_db_connection() -> sqlite3.Connection:
    """Create a SQLite connection with row access by column name."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    """Create required tables if they do not exist."""
    with get_db_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                amount REAL NOT NULL CHECK (amount >= 0),
                category TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT OR IGNORE INTO app_settings (key, value)
            VALUES ('monthly_budget', ?)
            """,
            (str(DEFAULT_MONTHLY_BUDGET),),
        )
        connection.commit()


def get_monthly_budget() -> float:
    """Read monthly budget from settings table with fallback safety."""
    with get_db_connection() as connection:
        row = connection.execute(
            "SELECT value FROM app_settings WHERE key = 'monthly_budget'"
        ).fetchone()

    if row is None:
        return DEFAULT_MONTHLY_BUDGET

    try:
        return float(row["value"])
    except (TypeError, ValueError):
        return DEFAULT_MONTHLY_BUDGET


def set_monthly_budget(value: float) -> None:
    """Persist monthly budget in settings table."""
    with get_db_connection() as connection:
        connection.execute(
            """
            INSERT INTO app_settings (key, value)
            VALUES ('monthly_budget', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (str(value),),
        )
        connection.commit()


def parse_expense_row(row: sqlite3.Row) -> dict[str, Any]:
    """Normalize DB rows for JSON responses."""
    return {
        "id": row["id"],
        "title": row["title"],
        "amount": float(row["amount"]),
        "category": row["category"],
        "created_at": row["created_at"],
    }


def fetch_all_expenses() -> list[dict[str, Any]]:
    with get_db_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, title, amount, category, created_at
            FROM expenses
            ORDER BY datetime(created_at) DESC, id DESC
            """
        ).fetchall()
    return [parse_expense_row(row) for row in rows]


def compute_summary(expenses: list[dict[str, Any]]) -> dict[str, Any]:
    monthly_budget = get_monthly_budget()
    total_spent = sum(expense["amount"] for expense in expenses)
    remaining_balance = monthly_budget - total_spent

    by_category: dict[str, float] = {}
    for expense in expenses:
        category = expense["category"]
        by_category[category] = by_category.get(category, 0.0) + expense["amount"]

    return {
        "monthly_budget": round(monthly_budget, 2),
        "total_spent": round(total_spent, 2),
        "remaining_balance": round(remaining_balance, 2),
        "category_totals": by_category,
    }


@app.route("/")
def index() -> str:
    expenses = fetch_all_expenses()
    summary = compute_summary(expenses)
    return render_template("index.html", expenses=expenses, summary=summary)


@app.get("/api/expenses")
def get_expenses() -> Any:
    expenses = fetch_all_expenses()
    summary = compute_summary(expenses)
    return jsonify({"expenses": expenses, "summary": summary}), 200


@app.post("/api/expenses")
def create_expense() -> Any:
    payload = request.get_json(silent=True) or {}

    title = str(payload.get("title", "")).strip()
    category = str(payload.get("category", "")).strip()

    try:
        amount = float(payload.get("amount", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "Amount must be a valid number."}), 400

    if not title:
        return jsonify({"error": "Title is required."}), 400
    if not category:
        return jsonify({"error": "Category is required."}), 400
    if amount <= 0:
        return jsonify({"error": "Amount must be greater than zero."}), 400

    created_at = datetime.utcnow().isoformat(timespec="seconds")

    with get_db_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO expenses (title, amount, category, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (title, amount, category, created_at),
        )
        connection.commit()

        row = connection.execute(
            """
            SELECT id, title, amount, category, created_at
            FROM expenses
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

    if row is None:
        return jsonify({"error": "Failed to create expense."}), 500

    expenses = fetch_all_expenses()
    summary = compute_summary(expenses)

    return jsonify({"expense": parse_expense_row(row), "summary": summary}), 201


@app.get("/api/budget")
def get_budget() -> Any:
    return jsonify({"monthly_budget": round(get_monthly_budget(), 2)}), 200


@app.patch("/api/budget")
def update_budget() -> Any:
    payload = request.get_json(silent=True) or {}

    try:
        monthly_budget = float(payload.get("monthly_budget", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "Monthly budget must be a valid number."}), 400

    if monthly_budget <= 0:
        return jsonify({"error": "Monthly budget must be greater than zero."}), 400

    set_monthly_budget(monthly_budget)

    expenses = fetch_all_expenses()
    summary = compute_summary(expenses)
    return jsonify({"message": "Budget updated.", "summary": summary}), 200


@app.delete("/api/expenses/<int:expense_id>")
def delete_expense(expense_id: int) -> Any:
    with get_db_connection() as connection:
        deleted = connection.execute(
            "DELETE FROM expenses WHERE id = ?", (expense_id,)
        ).rowcount
        connection.commit()

    if deleted == 0:
        return jsonify({"error": "Expense not found."}), 404

    expenses = fetch_all_expenses()
    summary = compute_summary(expenses)
    return jsonify({"message": "Expense deleted.", "summary": summary}), 200


init_db()


if __name__ == "__main__":
    app.run(debug=True)
