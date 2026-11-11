
import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()

mcp = FastMCP(name="My-Remote-Expense-Tracker")


# SQLite database file location

# Use a writable directory for SQLite
DB_DIR = Path(os.getenv("SQLITE_DB_DIR", "/tmp/expense_tracker"))
DB_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DB_DIR / "ExpenseTracker.db"



def get_connection():
    conn = sqlite3.connect(str(DB_PATH), timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


# Initialize database and Expense table
def initialize_database():
    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Expense (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT,
                note TEXT
            )
        """)

        conn.commit()

    finally:
        conn.close()


initialize_database()


@mcp.tool
def get_all_expense():
    """Return all expenses from the ExpenseTracker database."""

    conn = get_connection()

    try:
        cursor = conn.cursor()

        query = "SELECT * FROM Expense"
        cursor.execute(query)

        rows = cursor.fetchall()

        return [dict(row) for row in rows]

    finally:
        conn.close()


@mcp.tool
def get_expenses_by_date(min_date: str, max_date: str):
    """
    Retrieve expense records from the ExpenseTracker database
    within a specified date range.

    Use this tool when the user asks to view, list, or retrieve
    expenses for a particular date, between two dates, or during
    a specific time period such as a week, month, or year.

    Args:
        min_date (str): Start date in YYYY-MM-DD format.
            Expenses on or after this date are included.

        max_date (str): End date in YYYY-MM-DD format.
            Expenses on or before this date are included.

    Returns:
        list[dict]: List of matching expense records containing
            id, date, amount, category, subcategory, and note.

        Returns an empty list if no matching expenses are found.
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()

        query = """
            SELECT id, date, amount, category, subcategory, note
            FROM Expense
            WHERE date BETWEEN ? AND ?
            ORDER BY date DESC
        """

        cursor.execute(query, (min_date, max_date))

        rows = cursor.fetchall()

        expenses = []

        for row in rows:
            expenses.append({
                "id": row["id"],
                "date": row["date"],
                "amount": float(row["amount"]),
                "category": row["category"],
                "subcategory": row["subcategory"],
                "note": row["note"]
            })

        return expenses

    except Exception as e:
        return {"error": str(e)}

    finally:
        conn.close()


@mcp.tool
def add_expense(
    date: str,
    amount: float,
    category: str,
    subcategory: str,
    note: str
):
    """
    Add a new expense record to the ExpenseTracker database.

    Args:
        date (str): Expense date in YYYY-MM-DD format.
        amount (float): Expense amount.
        category (str): Main expense category.
        subcategory (str): Expense subcategory.
        note (str): Additional expense description.

    Returns:
        dict: Success message and newly created expense ID.
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()

        query = """
            INSERT INTO Expense (date, amount, category, subcategory, note)
            VALUES (?, ?, ?, ?, ?)
        """

        cursor.execute(
            query,
            (date, amount, category, subcategory, note)
        )

        expense_id = cursor.lastrowid

        conn.commit()

        return {
            "message": "Expense added successfully",
            "expense_id": expense_id
        }

    except Exception as e:
        conn.rollback()
        return {"error": str(e)}

    finally:
        conn.close()


if __name__ == "__main__":
    mcp.run(transport='http', host="0.0.0.0", port=8000)
