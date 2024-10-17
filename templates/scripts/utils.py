import os
from sqlalchemy import text
from sqlalchemy.orm import Session as SqlAlchemySession
from flask import g
from models import Decks  # Ensure the correct import path for your Decks model

def get_profile_pic_path(username, session_db):
    """Fetch the profile picture path for the given username."""
    if username is None:
        return "\\images\\profilePics\\Default.png"

    # Query to get user details
    query = text("SELECT ProfilePicture FROM Users WHERE Username = :username")
    user_details = session_db.execute(query, {'username': username}).fetchone()

    if user_details:
        profile_pic = user_details[0]
        return f"\\images\\profilePics\\{profile_pic}" if profile_pic else "\\images\\profilePics\\Default.png"
    
    return "\\images\\profilePics\\Default.png"  # Fallback if no details found


def get_decks_for_user(user_id, session_db):
    """Fetch decks for the specified user."""
    try:
        # Fetch decks for the user using the imported Decks model
        decks = session_db.query(Decks).filter(Decks.Owner == user_id).all()
        return [(deck.Deck, deck.UserDeckNum) for deck in decks]  # Return as list of tuples
    except Exception as e:
        print(f"Error fetching decks: {e}")  # Log the error
        return []  # Return an empty list on error


def get_user_id_by_username(username):
    """Fetch the user ID based on the username."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM Users WHERE Username = ?", (username,))
    result = cursor.fetchone()
    return result[0] if result else None


def get_user_details_by_username(username):
    """Fetch user details (id and profile picture) by username."""
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, ProfilePicture FROM Users WHERE Username = ?", (username,))
    result = cursor.fetchone()
    return result  # Returns (id, ProfilePic) if found, else None


def get_db():
    """Get a database connection from the Flask global context."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = SqlAlchemySession()  # Using SQLAlchemy session here
    return db
