# scripts/utils.py

import os
import sqlite3 
from sqlalchemy import create_engine, text
from flask import Flask, render_template, request, redirect, url_for, flash, session, g

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('databases/database.db')  # Connecting to SQLite
    return db

def get_profile_pic_path(username, session_db):
    if username is None:
        return "images/profilePics/Default.png"

    # Query to get user details
    query = text("SELECT ProfilePicture FROM Users WHERE Username = :username")
    user_details = session_db.execute(query, {'username': username}).fetchone()

    if user_details:
        profile_pic = user_details[0]
        return f"images/profilePics/{profile_pic}" if profile_pic else "images/profilePics/Default.png"
    
    return "images/profilePics/Default.png"  # Fallback if no details found


def get_decks_for_user(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT Deck, UserDeckNum FROM decks WHERE Owner = ?", (user_id,))
    return cursor.fetchall()

def get_user_id_by_username(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id FROM Users WHERE Username = ?", (username,))
    result = cursor.fetchone()
    return result[0] if result else None

def get_user_details_by_username(username):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, ProfilePicture FROM Users WHERE Username = ?", (username,))
    result = cursor.fetchone()
    return result  # Returns (id, ProfilePic) if found, else None