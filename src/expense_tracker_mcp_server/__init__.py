# import random
# from fastmcp import FastMCP

# mcp=FastMCP(name='my-first-mcp')

# @mcp.tool
# def roll_dice(n_dice: int) -> list[int]:
#     """
#     Roll one or more fair six-sided dice and return the results.

#     Use this tool whenever the user wants to roll dice or
#     generate random dice outcomes.

#     Args:
#         n_dice (int): Number of six-sided dice to roll.
#                       Must be a positive integer.

#     Returns:
#         list[int]: Results of the dice rolls, where each
#                    result is between 1 and 6.

#     Example:
#         n_dice = 3
#         Returns: [2, 5, 1]
#     """

#     if isinstance(n_dice, bool) or not isinstance(n_dice, int):
#         raise TypeError("n_dice must be an integer")

#     if n_dice <= 0:
#         raise ValueError("n_dice must be greater than zero")

#     return [random.randint(1, 6) for _ in range(n_dice)]


# @mcp.tool
# def add_two_numbers(first_number:int,second_number:int)->int:
#     '''do addition of two numbers and return their sum'''
#     return first_number + second_number

# if __name__ == '__main__':
#     mcp.run()





import os
import pyodbc
from dotenv import load_dotenv
from fastmcp import FastMCP
load_dotenv()

mcp = FastMCP(name='My-Expense-Tracker')


def get_connection(database=None, autocommit=False):

    server = os.getenv("SQL_SERVER")
    # database = database or os.getenv(
    #     "SQL_DATABASE", "BrandPulseDB"
    # )

    database='ExpenseTracker'

    if not server:
        raise ValueError("SQL_SERVER is missing from .env")

    connection_string = (
        "DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={server};"
        f"DATABASE={database};"
        "Trusted_Connection=yes;"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )

    return pyodbc.connect(
        connection_string,
        autocommit=autocommit,
        timeout=10
    )


@mcp.tool
def get_all_expense():
    '''return all the expenses'''
    conn = get_connection()
    cursor = conn.cursor()
    query="""select * from [dbo].[Expense]"""
    cursor.execute(query)
    return cursor.fetchall()



@mcp.tool
def get_expenses_by_date(min_date: str, max_date: str):
    """
    Retrieve expense records from the ExpenseTracker database within a specified date range.

    Use this tool when the user asks to view, list, or retrieve expenses
    for a particular date, between two dates, or during a specific time
    period such as a week, month, or year.

    Args:
        min_date (str): Start date of the expense search in YYYY-MM-DD format.
            Expenses recorded on or after this date are included.

        max_date (str): End date of the expense search in YYYY-MM-DD format.
            Expenses recorded on or before this date are included.

    Returns:
        list[dict]: List of matching expense records containing:
            - id: Unique expense identifier.
            - date: Date of the expense.
            - amount: Expense amount.
            - category: Main expense category.
            - subcategory: Expense subcategory.
            - note: Additional expense description.

        Returns an empty list if no matching expenses are found.
        Returns a dictionary containing an error message if the query fails.
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

        cursor.execute(query, min_date, max_date)

        rows = cursor.fetchall()

        expenses = []

        for row in rows:
            expenses.append({
                "id": row.id,
                "date": str(row.date),
                "amount": float(row.amount),
                "category": row.category,
                "subcategory": row.subcategory,
                "note": row.note
            })

        return expenses

    except Exception as e:
        return {"error": str(e)}

    finally:
        conn.close()


@mcp.tool
def add_expense(date, amount, category, subcategory, note):
    '''add expense into the expenses'''
    conn = get_connection()

    try:
        cursor = conn.cursor()

        query = """
            INSERT INTO Expense (date, amount, category, subcategory, note)
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?)
        """

        cursor.execute(
            query,
            date,
            amount,
            category,
            subcategory,
            note
        )

        expense_id = cursor.fetchone()[0]

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
    mcp.run()
    # pass
    # conn = get_connection()
    # cursor = conn.cursor()

    # data= get_all_brands(cursor=cursor)
    # print(data)
    # # try:
    # #     print("Successfully connected to SQL Server!")
    # #     print("Database:", conn.getinfo(pyodbc.SQL_DATABASE_NAME))
    # # finally:
    # #     conn.close()

