import os
import sqlite3
from flask import g, url_for
from sqlalchemy import text
from sqlalchemy.orm import Session as SqlAlchemySession
from templates.scripts.models import Decks

DATABASE_URI = 'databases/database.db'  # SQLite database file path

# Helper function to get a database connection
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE_URI)
    return db

def get_user_id_by_username(username):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT Id FROM Users WHERE Username = ?", (username,))
    user = cursor.fetchone()
    if user:
        return user[0]
    return None

def get_user_details_by_username(username):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users WHERE Username = ?", (username,))
    user = cursor.fetchone()
    return user

def get_decks_for_user(username):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Decks WHERE Owner = ?", (username))
    deckNumbers = cursor.fetchall()
    return deckNumbers

def get_profile_pic_path(username):
    user = get_user_details_by_username(username)
    if user and user[7]:  # Assuming ProfilePicture is the 8th column
        return url_for('static', filename=f'images/profilePics/{user[7]}')
    return url_for('static', filename='images/profilePics/Default.png')
