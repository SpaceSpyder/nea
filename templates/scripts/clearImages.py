import os
import sqlite3

def removeUnusedImages():
    # Path to the database
    dbPath = 'databases/database.db'

    # Path to the profile pictures directory
    profilePicsDir = 'templates/images/profilePics'

    # Connect to the database
    conn = sqlite3.connect(dbPath)
    cursor = conn.cursor()

    # Get all profile pictures from the database
    cursor.execute("SELECT ProfilePicture FROM Users")
    profilePicsInDB = {row[0] for row in cursor.fetchall()}

    # Close the database connection
    conn.close()

    # Get all files in the profile pictures directory
    allFiles = set(os.listdir(profilePicsDir))

    # Determine which files are not used as profile pictures
    unsuedFiles = allFiles - profilePicsInDB

    # Delete unused files
    for file in unsuedFiles:
        filePath = os.path.join(profilePicsDir, file)
        if os.path.isfile(filePath):
            os.remove(filePath)
            print(f"Deleted {filePath}")

    print("Cleanup complete.")