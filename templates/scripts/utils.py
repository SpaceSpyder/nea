import sqlite3
from flask import g, url_for, session
from datetime import datetime # date and time for account creation

databaseUri = "databases/database.db"  # SQLite database file path
defaultPicPath = "images/profilePics/Default.png"


# Helper function to get a database connection
def getDb():
    if "db" not in g:
        g.db = sqlite3.connect(
            databaseUri,
            detect_types=sqlite3.PARSE_DECLTYPES,
            timeout=10  # Increase the timeout to 10 seconds
        )
        g.db.row_factory = sqlite3.Row
    return g.db


def closeDb(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def getUserIdByUsername(username):
    try:
        conn = getDb()
        cursor = conn.cursor()
        cursor.execute("SELECT Id FROM Users WHERE Username = ?", (username,))
        userId = cursor.fetchone()
        return userId[0] if userId else None
    finally:
        cursor.close()


def getUserDetailsByUsername(username):
    try:
        conn = getDb()
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
    finally:
        cursor.close()


def getDecksForUser(username):
    try:
        conn = getDb()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Decks WHERE Owner = ?", (username,))
        decks = cursor.fetchall()
        return decks
    finally:
        cursor.close()


def getDeckForUser(username, deckId):
    try:
        conn = getDb()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Decks WHERE Owner = ? AND UserDeckNum = ?", (username, deckId))
        deck = cursor.fetchone()
        return deck
    finally:
        cursor.close()


def getProfilePicPath(username=None):
    if not username:
        # Return default profile picture path if no username is provided
        return defaultPicPath

    # Retrieve the profile picture for the specific user from the database
    with getDb() as conn:
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
        return defaultPicPath


def checkUsername():
    if "Username" not in session:  # Check if the user is logged in
        return None
    else:
        return session["Username"]  # Get the username from the session


def calculateRank(username):
    # Calculate the rank of the user based on the number of wins they have
    conn = getDb()
    cursor = conn.cursor()
    try:
        # Get the number of wins for the current user
        cursor.execute("SELECT COUNT(*) FROM UserStats WHERE GamesWon = ?", (username,))
        userWins = cursor.fetchone()[0]

        # Count how many users have more wins than the current user
        cursor.execute("""
            SELECT COUNT(DISTINCT GamesWon) 
            FROM UserStats 
            GROUP BY GamesWon 
            HAVING COUNT(*) > ?
        """, (userWins,))
        rank = cursor.fetchone()[0] + 1  # Rank is the count of users with more wins + 1

        return rank
    finally:
        cursor.close()

def GetDeckNames(username):
    deckNames = []

    try:
        # Connect to the database
        conn = sqlite3.connect("databases/database.db")
        cursor = conn.cursor()

        # Query to retrieve DeckName for the specified user
        cursor.execute("""
            SELECT DeckName
            FROM Decks
            WHERE Owner = ?
        """, (username,))

        # Fetch all results and append DeckName to the list
        rows = cursor.fetchall()
        for row in rows:
            deckNames.append(row[0])  # row[0] corresponds to the DeckName column

    except sqlite3.Error as e:
        print(f"Error: {str(e)}")
    
    finally:
        # Close the cursor and connection
        cursor.close()
        conn.close()

    return deckNames

def insertUser(username, password, email):
    defaultDeck = "Knight, DarkKnight, Boar, Cavalry, PossessedArmour, Dragon, BabyDragon, Monk, Wizard, Orc, Skeleton, Medusa, StrongMan, FireSpirit, Stranger, SwampMonster, Executioner, IceSpirit, Harpy, Bear"
    date = datetime.today().strftime("%Y-%m-%d")
    conn = getDb()
    try:
        with conn:
            cursor = conn.cursor()
            # Insert the new user into the Users table
            cursor.execute("""
                INSERT INTO Users (Username, Password, Email, DateCreated, ProfilePicture)
                VALUES (?, ?, ?, ?, "Default.png")
            """, (username, password, email, date))
            
            # Get the user ID of the newly inserted user
            cursor.execute("SELECT Id FROM Users WHERE Username = ?", (username,))
            user_id = cursor.fetchone()[0]
            
            # Insert a new record into the UserStats table
            cursor.execute("""
                INSERT INTO UserStats (UserId, GamesPlayed, GamesWon, DateCreated, FavouriteCard)
                VALUES (?, 0, 0, ?, "/images/CardPictures/Knight.png")
            """, (user_id, date))

            cursor.execute("""
                INSERT INTO Decks (Owner, UserDeckNum, Deck)
                VALUES (?, 1, ?)
            """, (username, defaultDeck))

    except sqlite3.OperationalError as e:
        print(f"Error: {e}")  # Error handling
        raise
    finally:
        conn.close()  # Close the database connection