# scripts/utils.py

import os
from sqlalchemy import create_engine, text

def get_profile_pic_path(username, session_db):
    # Query to get user details
    query = text("SELECT ProfilePicture FROM Users WHERE Username = :username")
    user_details = session_db.execute(query, {'username': username}).fetchone()

    if user_details:
        profile_pic = user_details[0]
        return f"images/profilePics/{profile_pic}" if profile_pic else "images/profilePics/Default.png"
    else:
        return "images/profilePics/Default.png"
