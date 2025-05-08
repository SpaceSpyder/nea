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
        cursor.execute("SELECT Id FROM Users WHERE Username = ?", (username,)) # Get user ID by username
        userId = cursor.fetchone()
        return userId[0] if userId else None
    except Exception as e:
        print(f"Error getting user ID: {str(e)}")
        return None


def getUserDetailsByUsername(username):
    conn = getDb()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE Username = ?", (username,)) # Get all user details
        user = cursor.fetchone()
        if user: # If user exists, store details in session
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
        cursor.execute("SELECT * FROM Decks WHERE Owner = ?", (username,)) # Get all decks for the user
        decks = cursor.fetchall()
        return decks
    except Exception as e:
        print(f"Error getting decks: {str(e)}")
        return []


def getDeckForUser(username, deckId=None):
    conn = getDb()
    try:
        cursor = conn.cursor()
        if deckId is None:
            cursor.execute("SELECT CurrentDeck FROM Users WHERE Username = ?", (username,)) # Get the current deck ID for the user
            deckIdRow = cursor.fetchone()
            if not deckIdRow:
                return []
            deckId = deckIdRow[0]
        cursor.execute(
            "SELECT Deck FROM Decks WHERE Owner = ? AND UserDeckNum = ?",
            (username, deckId)
        ) # Get the deck for the user
        deckRow = cursor.fetchone()
        if deckRow:
            return deckRow[0].split(", ")
        else:
            return []
    except Exception as e:
        print(f"Error getting deck: {str(e)}")
        return []
    finally:
        cursor.close()
        conn.close()


def getProfilePicPath(username=None):
    if not username:
        return defaultPicPath

    try:
        conn = getDb()
        cursor = conn.cursor()
        cursor.execute("SELECT ProfilePicture FROM Users WHERE Username = ?", (username,)) # Get the profile picture for the user
        result = cursor.fetchone()
        if result and result[0]:
            from flask import has_app_context
            if has_app_context():
                return url_for('static', filename=f'images/profilePics/{result[0]}')
        # Fallback to default if no result or not in app context
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
        cursor.execute("SELECT COUNT(*) FROM UserStats WHERE GamesWon = ?", (username,)) # Get the number of wins
        userWins = cursor.fetchone()[0]

        # Count how many users have more wins than the current user
        cursor.execute("""
            SELECT COUNT(DISTINCT GamesWon) 
            FROM UserStats 
            GROUP BY GamesWon 
            HAVING COUNT(*) > ?
        """, (userWins,)) # Count users with more wins
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
        """, (username,)) # Fetch all deck names for the user

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
            userID = cursor.fetchone()[0]
            
            # Insert a new record into the UserStats table
            cursor.execute("""
                INSERT INTO UserStats (UserId, GamesPlayed, GamesWon, DateCreated, FavouriteCard)
                VALUES (?, 0, 0, ?, "/images/CardPictures/Knight.png")
            """, (userID, date))

            cursor.execute("""
                INSERT INTO Decks (Owner, UserDeckNum, Deck, DeckName)
                VALUES (?, 1, ?, "Default Deck")
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
            """, (userId,)) # Increase the number of games played
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
            """, (userId,)) # Increase the number of games won
    except sqlite3.OperationalError as e:
        print(f"Error increasing games won: {e}")
        raise