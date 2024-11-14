import os
import sqlite3
from flask import g, url_for, session, redirect

DATABASE_URI = 'databases/database.db'  # SQLite database file path

# Helper function to get a database connection
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            DATABASE_URI,
            detect_types=sqlite3.PARSE_DECLTYPES,
            timeout=10  # Increase the timeout to 10 seconds
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(exception):
    db = g.pop('db', None)
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
            session['Id'] = user[0]
            session['Username'] = user[1]
            session['Email'] = user[3]
            session['DateCreated'] = user[4]
            session['ProfilePicture'] = user[5]
            session['CurrentDeck'] = user[6]
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
    # Default profile picture path
    default_pic_path = url_for('static', filename='images/profilePics/Default.png')
    print()
    print(username)
    print()
    if not username:
        # Return default profile picture path if no username is provided
        return default_pic_path

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
        return default_pic_path

def check_username():
    if 'Username' not in session:  # Check if the user is logged in
        return redirect(url_for('login'))  # Redirect to login if not logged in
    else:
        return session['Username']  # Get the username from the session
