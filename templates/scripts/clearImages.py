import os
import sqlite3

def removeUnusedImages():
    # Path to the database
    db_path = 'databases/database.db'

    # Path to the profile pictures directory
    profile_pics_dir = 'templates/images/profilePics'

    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get all profile pictures from the database
    cursor.execute("SELECT ProfilePicture FROM Users")
    profile_pics_in_db = {row[0] for row in cursor.fetchall()}

    # Close the database connection
    conn.close()

    # Get all files in the profile pictures directory
    all_files = set(os.listdir(profile_pics_dir))

    # Determine which files are not used as profile pictures
    unused_files = all_files - profile_pics_in_db

    # Delete unused files
    for file in unused_files:
        file_path = os.path.join(profile_pics_dir, file)
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"Deleted {file_path}")

    print("Cleanup complete.")