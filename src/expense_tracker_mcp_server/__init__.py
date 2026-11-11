
import os
import aiosqlite

from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastmcp import FastMCP

load_dotenv()


# --------------------------------------
# DATABASE CONFIGURATION
# --------------------------------------

DB_DIR = Path(
    os.getenv("SQLITE_DB_DIR", "/tmp/expense_tracker")
)

DB_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = DB_DIR / "ExpenseTracker.db"


# --------------------------------------
# ASYNC DATABASE CONNECTION
# --------------------------------------

@asynccontextmanager
async def get_connection():

    async with aiosqlite.connect(
        str(DB_PATH),
        timeout=10
    ) as conn:

        conn.row_factory = aiosqlite.Row

        yield conn


# --------------------------------------
# ASYNC DATABASE INITIALIZATION
# --------------------------------------

async def initialize_database():

    async with get_connection() as conn:

        # Enable WAL mode for better concurrency
        await conn.execute("PRAGMA journal_mode=WAL")

        await conn.execute("""
            CREATE TABLE IF NOT EXISTS Expense (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT,
                note TEXT
            )
        """)

        await conn.commit()


# --------------------------------------
# MCP SERVER LIFESPAN
# --------------------------------------

@asynccontextmanager
async def app_lifespan(server: FastMCP):

    # Initialize database at server startup
    await initialize_database()

    yield {}


mcp = FastMCP(
    name="My-Remote-Expense-Tracker",
    lifespan=app_lifespan
)


# --------------------------------------
# TOOL 1: GET ALL EXPENSES
# --------------------------------------

@mcp.tool
async def get_all_expense():
    """
    Retrieve all expense records from the
    ExpenseTracker database.

    Returns:
        list[dict]: All expense records.
    """

    async with get_connection() as conn:

        query = "SELECT * FROM Expense"

        async with conn.execute(query) as cursor:
            rows = await cursor.fetchall()

        return [dict(row) for row in rows]


# --------------------------------------
# TOOL 2: GET EXPENSES BY DATE
# --------------------------------------

@mcp.tool
async def get_expenses_by_date(
    min_date: str,
    max_date: str
):
    """
    Retrieve expenses within a specified date range.

    Use this tool when users ask to view expenses
    for a particular day, week, month, year, or
    between two dates.

    Args:
        min_date (str): Start date in YYYY-MM-DD format.
            Expenses on or after this date are included.

        max_date (str): End date in YYYY-MM-DD format.
            Expenses on or before this date are included.

    Returns:
        list[dict]: Matching expense records.
        Returns an empty list if none are found.
    """

    async with get_connection() as conn:

        try:
            query = """
                SELECT id, date, amount,
                       category, subcategory, note
                FROM Expense
                WHERE date BETWEEN ? AND ?
                ORDER BY date DESC
            """

            async with conn.execute(
                query,
                (min_date, max_date)
            ) as cursor:

                rows = await cursor.fetchall()

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


# --------------------------------------
# TOOL 3: ADD EXPENSE
# --------------------------------------

@mcp.tool
async def add_expense(
    date: str,
    amount: float,
    category: str,
    subcategory: str,
    note: str
):
    """
    Add a new expense record to the ExpenseTracker database.

    Use this tool when users want to record a new expense.

    Args:
        date (str): Expense date in YYYY-MM-DD format.
        amount (float): Expense amount.
        category (str): Main expense category.
        subcategory (str): Expense subcategory.
        note (str): Additional expense description.

    Returns:
        dict: Success message and newly created expense ID.
    """

    async with get_connection() as conn:

        try:
            query = """
                INSERT INTO Expense
                (date, amount, category, subcategory, note)
                VALUES (?, ?, ?, ?, ?)
            """

            async with conn.execute(
                query,
                (
                    date,
                    amount,
                    category,
                    subcategory,
                    note
                )
            ) as cursor:

                expense_id = cursor.lastrowid

            await conn.commit()

            return {
                "message": "Expense added successfully",
                "expense_id": expense_id
            }

        except Exception as e:

            await conn.rollback()

            return {"error": str(e)}


# --------------------------------------
# RUN REMOTE MCP SERVER
# --------------------------------------

if __name__ == "__main__":

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=8000
    )
