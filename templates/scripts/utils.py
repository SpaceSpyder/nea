import os
import sqlite3
from flask import g, url_for, session

DATABASE_URI = "databases/database.db"  # SQLite database file path
DEFAULT_PIC_PATH = "images/profilePics/Default.png"


# Helper function to get a database connection
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(
            DATABASE_URI,
            detect_types=sqlite3.PARSE_DECLTYPES,
            timeout=10  # Increase the timeout to 10 seconds
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def get_user_id_by_username(username):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT Id FROM Users WHERE Username = ?", (username,))
        user = cursor.fetchone()
        return user[0] if user else None
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
        return None
    finally:
        cursor.close()


def get_user_details_by_username(username):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE Username = ?", (username,))
        user = cursor.fetchone()
        if user:
            session["Id"] = user[0]
            session["Username"] = user[1]
            session["Email"] = user[3]
            session["DateCreated"] = user[4]
            session["ProfilePicture"] = user[5]
            session["CurrentDeck"] = user[6]
        return user
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
        return None
    finally:
        cursor.close()


def get_decks_for_user(username):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Decks WHERE Owner = ?", (username,))
        return cursor.fetchall()
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
        return []
    finally:
        cursor.close()


def get_deck_for_user(username, deck_id):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Decks WHERE Owner = ? AND DeckId = ?", (username, deck_id))
        return cursor.fetchall()
    except sqlite3.DatabaseError as e:
        print(f"Database error: {e}")
        return []
    finally:
        cursor.close()


def get_profile_pic_path(username=None):
    if not username:
        # Return default profile picture path if no username is provided
        return DEFAULT_PIC_PATH

    # Retrieve the profile picture for the specific user from the database
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT ProfilePicture FROM Users WHERE Username = ?", (username,))
            result = cursor.fetchone()
        finally:
            cursor.close()

    # Return the user's profile picture path if it exists, otherwise return the default path
    if result and result[0]:
        return url_for('static', filename=f'images/profilePics/{result[0]}')
    else:
        return DEFAULT_PIC_PATH


def check_username():
    if 'Username' not in session:  # Check if the user is logged in
        return None
    else:
        return session['Username']  # Get the username from the session


def calculate_rank(username):
    # Calculate the rank of the user based on the number of wins they have
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Get the number of wins for the current user
        cursor.execute("SELECT COUNT(*) FROM UserStats WHERE GamesWon = ?", (username,))
        user_wins = cursor.fetchone()[0]

        # Count how many users have more wins than the current user
        cursor.execute("""
            SELECT COUNT(DISTINCT GamesWon) 
            FROM UserStats 
            GROUP BY GamesWon 
            HAVING COUNT(*) > ?
        """, (user_wins,))
        rank = cursor.fetchone()[0] + 1  # Rank is the count of users with more wins + 1

        return rank
    finally:
        cursor.close()