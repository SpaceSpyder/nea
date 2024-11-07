import os
import sqlite3
from flask import g, url_for, session
#from sqlalchemy import text
#from sqlalchemy.orm import Session as SqlAlchemySession
from templates.scripts.models import Decks

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
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT Id FROM Users WHERE Username = ?", (username,))
        user = cursor.fetchone()
        if user:
            return user[0]
        return None
    finally:
        cursor.close()

def get_user_details_by_username(username):
    conn = get_db()
    cursor = conn.cursor()
    try:
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
    finally:
        cursor.close()

def get_decks_for_user(username):
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM Decks WHERE Owner = ?", (username,))
        return cursor.fetchall()
    finally:
        cursor.close()

def get_deck_for_user(username, deck_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Decks WHERE Owner = ? AND DeckId = ?", (username,deck_id))
    decks = cursor.fetchall()
    return decks

def get_profile_pic_path(username):
    profile_pic = session.get('ProfilePicture')
    return url_for('static', filename=f'images/profilePics/{profile_pic}')



# def get_profile_pic_path(username):
#     user = get_user_details_by_username(username)
#     if user and len(user) > 5:  # Ensure the tuple has enough elements
#         profile_pic = user[5]  # Assuming ProfilePicture is the 6th column
#         if profile_pic:
#             return url_for('static', filename=f'images/profilePics/{profile_pic}')
#     return url_for('static', filename='images/profilePics/Default.png')
