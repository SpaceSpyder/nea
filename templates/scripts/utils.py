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
    conn = getDb()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT Id FROM Users WHERE Username = ?", (username,))
        userId = cursor.fetchone()
        return userId[0] if userId else None
    except Exception as e:
        print(f"Error getting user ID: {str(e)}")
        return None


def getUserDetailsByUsername(username):
    conn = getDb()
    try:
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
    except Exception as e:
        print(f"Error getting user details: {str(e)}")


def getDecksForUser(username):
    conn = getDb()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Decks WHERE Owner = ?", (username,))
        decks = cursor.fetchall()
        return decks
    except Exception as e:
        print(f"Error getting decks: {str(e)}")
        return []


def getDeckForUser(username, deckId):
    conn = getDb()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Decks WHERE Owner = ? AND UserDeckNum = ?", (username, deckId))
        deck = cursor.fetchone()
        return deck
    except Exception as e:
        print(f"Error getting deck: {str(e)}")
        return None


def getProfilePicPath(username=None):
    if not username:
        # Return default profile picture path if no username is provided
        return defaultPicPath

    # Retrieve the profile picture for the specific user from the database
    conn = getDb()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT ProfilePicture FROM Users WHERE Username = ?", (username,))
        result = cursor.fetchone()
        
        # Return the user's profile picture path if it exists, otherwise return the default path
        if result and result[0]:
            from flask import has_app_context
            if has_app_context():
                return url_for('static', filename=f'images/profilePics/{result[0]}')
            return defaultPicPath
        return defaultPicPath
    except Exception as e:
        print(f"Error getting profile picture: {str(e)}")
        return defaultPicPath


def checkUsername():
    if "Username" not in session:  # Check if the user is logged in
        return None
    else:
        return session["Username"]  # Get the username from the session


def calculateRank(username):
    # Calculate the rank of the user based on the number of wins they have
    conn = getDb()
    try:
        cursor = conn.cursor()
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
    except Exception as e:
        print(f"Error calculating rank: {str(e)}")
        return 0


def GetDeckNames(username):
    deckNames = []
    conn = getDb()
    try:
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
    except Exception as e:
        print(f"Error getting deck names: {str(e)}")
    
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
        print(f"Error inserting user: {e}")
        raise


def increaseGamesPlayed(username):
    userId = getUserIdByUsername(username)
    conn = getDb()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE UserStats 
                SET GamesPlayed = GamesPlayed + 1
                WHERE UserId = ?
            """, (userId,))
    except sqlite3.OperationalError as e:
        print(f"Error increasing games played: {e}")
        raise


def increaseGamesWon(username):
    userId = getUserIdByUsername(username)
    conn = getDb()
    try:
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE UserStats 
                SET GamesWon = GamesWon + 1
                WHERE UserId = ?
            """, (userId,))
    except sqlite3.OperationalError as e:
        print(f"Error increasing games won: {e}")
        raise