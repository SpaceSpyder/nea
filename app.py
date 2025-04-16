from datetime import timedelta # date and time for account creation
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash # password hashing
from werkzeug.utils import secure_filename # for secure file uploads
import sqlite3 # for database operations
import os  # Import os module
import json
import binascii # for unique session key

from templates.scripts.cropImage import (cropAndShowImage)
from templates.scripts.clearImages import (removeUnusedImages)
from templates.scripts.utils import ( # python functions from utils.py
    getProfilePicPath,
    getUserIdByUsername,
    getUserDetailsByUsername,
    getDecksForUser,
    getDb,
    checkUsername,
    calculateRank,
    insertUser,
)
from dataclasses import dataclass, asdict
from moduels import Game, GameBoard, Card, Player # Import Game, GameBoard, and Card classes

# pip install flask werkzeug
# pip install pillow
# python -m flask --version

# First, install Flask-Session:
# pip install flask-session


# Database setup
DATABASE_URI = "databases/database.db"
DEFAULT_PIC_PATH = "images/profilePics/Default.png"

# Flask app setup
app = Flask(__name__, static_folder="templates", static_url_path="") # Set the static folder to the templates directory
app.config["SECRET_KEY"] = binascii.hexlify(os.urandom(24)).decode('utf-8') # Generate a random secret key

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

app.config["UPLOAD_FOLDER"] = os.path.join("templates", "images", "profilePics") # Set the upload folder
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=1)  # session timeout after 1 hour


@app.route("/home")
@app.route("/index")
@app.route("/")
def index():
    username = session.get("Username") # get username from session
    profilePicPath = getProfilePicPath(username) if username else getProfilePicPath()
    return render_template("index.html", profile_pic=profilePicPath)


@app.route("/howToPlay")
def howToPlay():
    username = session.get("Username")
    profilePicPath = getProfilePicPath(username) if username else getProfilePicPath()
    return render_template("howToPlay.html", profile_pic=profilePicPath)


# -------- login and sign up ---------


@app.route("/login", methods=["POST", "GET"])
def login():
    profilePicPath = DEFAULT_PIC_PATH # Default profile picture path

    # Check if the user is already logged in
    if "Username" in session:
        flash("You are already logged in!", "info")
        return redirect(url_for("index")) # Redirect to the index page

    if request.method == "POST":
        # get username and password from html form
        username = request.form["username"]
        password = request.form["password"]

        conn = getDb()  # Connects to the database
        cursor = conn.cursor()  # Creates a cursor object to interact with the database
        cursor.execute("SELECT * FROM Users WHERE Username = ?", (username,))  # Executes a query to find the user by username
        result = cursor.fetchone()  # Fetches the first result from the query

        if result and check_password_hash(result[2], password):  # Checks if the user exists and the password is correct
            getUserDetailsByUsername(username)  # Retrieves user details by username
            flash("Logged in successfully!", "success")  # Displays a success message
            return redirect(url_for("index"))  # Redirects to the index page
        else:
            flash("Incorrect username / password!", "error")  # Displays an error message if login fails

    return render_template("login.html",profile_pic=profilePicPath)


@app.route("/signUp", methods=["GET", "POST"])
def signUp():

    # if logged in send back to homepage
    if "Username" in session: 
        flash("You are already signed up!", "info")
        return redirect(url_for("index"))

    profilePicPath = DEFAULT_PIC_PATH  # Default profile picture path

    if request.method == "POST": # when the form is submitted
        username = request.form["username"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"]) # makes db more secure
        
        try: # try to insert the user into the database
            insertUser(username, password, email)
            session["Username"] = username
            session.permanent = True
            flash("Signed up successfully!", "success")
            return redirect(url_for("index"))

        except sqlite3.IntegrityError as e: # if the username already exists
            if "UNIQUE constraint failed: Users.Username" in str(e):
                flash("Username already exists. Please choose a different username.", "error")
            else: # unknown error
                flash("ERROR signing up. Please try again.", "error")
                print(f"Error: {str(e)}", "error")
            return render_template("signUp.html", profile_pic=profilePicPath)

    return render_template("signUp.html", profile_pic=profilePicPath)


@app.route("/logout")
def logout():
    session.clear() # clears session
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


# -------- profile stuff ---------


@app.route("/profile")
def profile():
    if not session.get("Username"):
        return redirect(url_for("login"))
    profilePicPath = getProfilePicPath(session["Username"])

    return render_template("profile.html", profile_pic=profilePicPath)



@app.route("/profile/stats", methods=["GET"])
@app.route("/profile/stats/<username>", methods=["GET"])
@app.route("/stats", methods=["GET"])
@app.route("/stats/<username>", methods=["GET"])
def stats(username=None):
    if not session.get("Username"):  # Check if the user is logged in
        return redirect(url_for("login"))
    
    # If username is not provided in the URL, use the logged-in user's username
    if username is None:
        username = session["Username"]

    accountPicPath = getProfilePicPath(username) if username else getProfilePicPath() # pfp from the url
    accountUsername = username # username from the url
    profilePicPath = getProfilePicPath(session["Username"])  # pfp from session
    sessionUsername = session["Username"]  # username from session

    # db connection
    conn = getDb()
    cursor = conn.cursor()

    try: # get user stats
        userId = getUserId(cursor, username)
        if userId is None: # if user does not exist
            flash("User does not exist.", "error")
            return redirect(url_for("profile"))
        statsData = getUserStats(cursor, userId, username) # user stats
    finally: # close db connection
        cursor.close()
        conn.close()

    return render_template("stats.html", profile_pic=profilePicPath, stats=statsData, username=sessionUsername, account_pic=accountPicPath, account_username=accountUsername)

def getUserId(cursor, username): # get user id from username
    cursor.execute("SELECT Id FROM Users WHERE Username = ?", (username,))
    result = cursor.fetchone()
    return result[0] if result else None

def getUserStats(cursor, userId, username):
    if userId:
        # Query to get user statistics from the database
        cursor.execute("SELECT GamesPlayed, GamesWon, DateCreated, FavouriteCard FROM UserStats WHERE UserId = ?", (userId,))
        userStats = cursor.fetchone()
        if userStats:
            rank = calculateRank(username)  # Calculate the rank based on the username
            return {
                "Rank": rank,
                "GamesPlayed": userStats[0],  # Number of games played
                "GamesWon": userStats[1],  # Number of games won
                "DateCreated": userStats[2],  # Date the user account was created
                "FavouriteCard": userStats[3]  # User's favorite card
            }
    # Return default values if user stats are not found
    return {"Rank": "N/A", "GamesPlayed": 0, "GamesWon": 0, "DateCreated": "N/A", "FavouriteCard": "N/A"}

@app.route("/decks/<username>", methods=["GET", "POST"])
@app.route("/profile/decks/<username>", methods=["GET", "POST"])
def showDecks(username):
    if not session.get("Username"):  # check if the user is logged in
        return redirect(url_for("login"))
    profilePicPath = getProfilePicPath(session["Username"])  # get pfp
    session_username = session["Username"]  # get username

    # Check if the user exists
    user_id = getUserIdByUsername(username)
    if not user_id:
        flash("User not found", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        selected_cards = request.form.get("selectedCards")
        if selected_cards:
            #selected_cards = json.loads(selected_cards)
            
            flash("New deck created successfully!", "success")
            return redirect(url_for("showDecks", username=username))

    accountUsername = username # username from the url
    
    decks = getDecksForUser(username) # Retrieve decks for the specified username

    # Fetch the current deck number from the Users table
    try:
        conn = sqlite3.connect("databases/database.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT CurrentDeck FROM Users
            WHERE Username = ?
        """, (username,))
        current_deck_num = cursor.fetchone()
        if current_deck_num:
            current_deck_num = current_deck_num[0]
        else:
            current_deck_num = None

        # Fetch the current deck from the Decks table
        if current_deck_num is not None:
            cursor.execute("""
                SELECT Deck FROM Decks
                WHERE Owner = ? AND UserDeckNum = ?
            """, (username, current_deck_num))
            deck_row = cursor.fetchone()
            if deck_row:
                current_deck = deck_row[0].split(", ")
            else:
                current_deck = []
        else:
            current_deck = []
    except sqlite3.Error as e:
        flash(f"Error: check server terminal", "error")
        print(f"SQLite error: {str(e)}")
        current_deck = []
    finally:
        cursor.close()
        conn.close()

    return render_template("decks.html", profile_pic=profilePicPath, username=session_username, decks=decks, current_deck=current_deck, account_username=accountUsername)



@app.route("/profile/changePfp", methods=["GET", "POST"])
def change_profile_pic():
    if not session.get("Username"):  # check if the user is logged in
        return redirect(url_for("login"))
    profilePicPath = getProfilePicPath(session["Username"])  # get pfp
    username = session["Username"]  # get username

    # Handle the POST request to change the profile picture
    if request.method == "POST":
        # Check if the profile picture file is in the request
        if "profile_pic" not in request.files:
            flash("No file part", "error")
            return redirect(url_for("profile"))

        file = request.files["profile_pic"]
        # Check if a file is selected
        if file.filename == "":
            flash("No selected file", "error")
            return redirect(url_for("profile"))

        if file:
            # Secure the filename and set the upload folder
            filename = secure_filename(file.filename)
            app.config["UPLOAD_FOLDER"] = os.path.join("templates", "images", "profilePics")

            # Create the upload folder if it doesn't exist
            if not os.path.exists(app.config["UPLOAD_FOLDER"]):
                os.makedirs(app.config["UPLOAD_FOLDER"])

            # Save the file to the upload folder
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

            # Crop and save the uploaded image
            cropAndShowImage(filename)

            # Update the user's profile picture in the database
            conn = getDb()
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE Users SET ProfilePicture = ? WHERE Username = ?", (filename, username))
                conn.commit()
                flash("Profile picture updated successfully!", "success")
            except sqlite3.Error as e:
                conn.rollback()
                flash(f"Error: {str(e)}", "error")

            removeUnusedImages()
            return redirect(url_for("profile"))

    # Render the change profile picture template
    return render_template("changePfp.html", profile_pic=profilePicPath)




@app.route("/testGame")
def testGame():
    # Check if the user is logged in
    username = checkUsername()
    if username:
        profilePicPath = getProfilePicPath(username) if username else getProfilePicPath()  # get profile picture path from the user details
        return render_template("game.html", profile_pic=profilePicPath)
    else:
        return render_template("game.html")
        return redirect(url_for("login"))  # Redirect response if the user is not logged in



@app.route("/testGame2", methods=["GET"])
def testGame2():
    if not session.get("Username"):  # check if the user is logged in
        return redirect(url_for("login"))
    username = session.get("Username")
    return render_template("game2.html", username=username)
 
 
@app.route("/testGame2/getCurrentGame", methods=["GET"])
def getCurrentGame():
        global globalGameCount
        global globalGameList
        dumpGlobalState()
        username = session.get("Username")
        if username == None:  # check if the user is logged in
            return '{"status" : "GAME_DELETED"}'  # Check if user is logged in

        if session.get("CurrentGame"): 
            game = globalGameList[(session["CurrentGame"] - 1)]
            if (game and game.player1 and game.player2 and game.player1.health <= 0 or game.player2.health <= 0):
                # End the game if either player is dead
                winner = "player1" if game.player2.health <= 0 else "player2"
                return jsonify({"status": "game_over", "winner": winner, "currentGame":game}), 200  
            return json.dumps(asdict(game))
        #session["CurrentGame"] = globalGameCount
 
        for game in globalGameList:
            if (game.player2 == None ) and username != game.player1.username:
                player2 = Player(username, False, 10, 5)  # Create player2 with default health and mana
                game.player2 = player2  # Assign user to player2 if slot is empty
                dumpGlobalState()
                session["CurrentGame"] = globalGameCount
                session.modified = True
                game.player1.health = 10
                game.player2.health = 10
                return '{"isPlayer1" : false}'  # User is player2
 
        globalGameCount += 1
        player1 = Player(username, True, 10, 5)  # Create player1 with default health and mana
        newGame = Game(player1, None, globalGameCount, 0)
        globalGameList.append(newGame)
        session["CurrentGame"] = globalGameCount
        dumpGlobalState()
        session.modified = True
        return '{"isPlayer1" : true}'  # User is player1
 
 
@app.route("/testGame2/waitForSecondPlayer", methods=["GET"])
def waitForSecondPlayer():
    global globalGameCount
    global globalGameList
    dumpGlobalState()
    if session.get("CurrentGame"): 
         game = globalGameList[(session["CurrentGame"] - 1)]
         return '{"player2Found" :"' + str(game.player2.username) + '"}'  # Return player2's username
    return '{"ERROR no current game" : true}'  # Error if no current game

@app.route("/testGame2/receiveEndTurn", methods=["POST"])
def receiveEndTurn():
    print("Received end turn")
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Invalid data"}), 400

        game_id = session.get("CurrentGame")
        if game_id is None:
            return jsonify({"status": "error", "message": "No current game"}), 400

        global globalGameList
        game = globalGameList[game_id - 1]
        game_board_data = data.get("gameBoard", {})

        try:
            game.gameBoard = GameBoard(
                p1Attack=[Card(**card) for card in game_board_data.get("p1Attack", [])],
                p1Defence=[Card(**card) for card in game_board_data.get("p1Defence", [])],
                p2Attack=[Card(**card) for card in game_board_data.get("p2Attack", [])],
                p2Defence=[Card(**card) for card in game_board_data.get("p2Defence", [])],
                p1bank=[Card(**card) for card in game_board_data.get("p1bank", [])],
                p2bank=[Card(**card) for card in game_board_data.get("p2bank", [])]
            )
            runAttackSequence(game)
            
            game.roundNum = data.get("roundNum", game.roundNum)
        except Exception as e:
            print(f"Error updating game board: {e}")
            return jsonify({"status": "error", "message": "Failed to update game board"}), 500

        response = {"status": "success", "message": "Game state updated", "game": asdict(game)}
        return jsonify(response), 200
    except Exception as e:
        print(f"Error in receiveEndTurn: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500


# -------- flask functions --------


@app.route("/testGame2/deleteGame", methods=["POST"])
def deleteGame():
    try:
        username = session.get("Username")
        if not username:
            return jsonify({"status": "NOT_LOGGED_IN", "message": "You are not logged in"})

        game_id = session.get("CurrentGame")
        if game_id is None:
            session.pop("CurrentGame", None)
            session.pop("InGame", None)
            return jsonify({"status": "success", "message": "No active game to delete", "redirect": "/index"})

        global globalGameList

        if game_id < 1 or game_id > len(globalGameList):
            session.pop("CurrentGame", None)
            session.pop("InGame", None)
            return jsonify({"status": "success", "message": "Invalid game ID cleared", "redirect": "/index"})

        game = globalGameList[game_id - 1]

        if username != game.player1.username and username != game.player2.username:
            return jsonify({"status": "error", "message": "You are not a player in this game"})

        player1 = game.player1
        player2 = game.player2

        # Remove the game from the list
        globalGameList.pop(game_id - 1)

        # Adjust game IDs for all games with higher IDs
        for i in range(game_id - 1, len(globalGameList)):
            globalGameList[i].gameId -= 1

        # Adjust the global game count
        global globalGameCount
        globalGameCount = len(globalGameList)

        # Clear current game from THIS user's session
        session.pop("CurrentGame", None)
        session.pop("InGame", None)

        # Clear the other player's session
        if player1 and player1.username != username:
            for sess_key, sess_data in session.items():
                if sess_data.get("Username") == player1:
                    session.pop(sess_key, None)
                    break

        if player2 and player2.username != username:
            for sess_key, sess_data in session.items():
                if sess_data.get("Username") == player2.username:
                    session.pop(sess_key, None)
                    break

        dumpGlobalState()

        return jsonify({
            "status": "success",
            "message": "Game deleted successfully",
            "redirect": "/index"
        })
    except Exception as e:
        print(f"Error in deleteGame: {e}")
        return jsonify({"status": "error", "message": str(e)})


@app.route("/modifyDeck/<username>", methods=["POST"])
def modifyDeck(username):
    if not session.get("Username"):  # check if the user is logged in
        return redirect(url_for("login"))

    selectedCards = request.form.get("selectedCards")
    selectedDeck = request.form.get("deck")
    deckName = request.form.get("deckNameInput")
    print(deckName)

    if selectedDeck == "create":
        conn = getDb()
        cursor = conn.cursor()
        try:
            with conn:
                # Determine the next UserDeckNum for the user
                cursor.execute("""
                    SELECT COALESCE(MAX(UserDeckNum), 0) + 1
                    FROM Decks
                    WHERE Owner = ?
                """, (username,))
                user_deck_num = cursor.fetchone()[0]

                # Insert the new deck into the Decks table
                cursor.execute("""
                    INSERT INTO Decks (Owner, UserDeckNum, Deck, DeckName)
                    VALUES (?, ?, ?, ?)
                """, (username, user_deck_num, selectedCards, deckName))
                flash("New deck created successfully!", "success")
        except sqlite3.Error as e:
            flash(f"Error: {e}", "error")
            print(f"SQLite error: {str(e)}")
        finally:
            cursor.close()
    
    else:
        # change current deck of the user
        conn = getDb()
        cursor = conn.cursor()
        try:
            with conn:
                cursor.execute("""
                    UPDATE Users
                    SET CurrentDeck = ?
                    WHERE Username = ?
                """, (selectedDeck, username))
                flash("Current deck updated successfully!", "success")
        except sqlite3.Error as e:
            flash(f"Error: check server terminal", "error")
            print(f"SQLite error: {str(e)}")
        finally:
            cursor.close()

    return redirect(url_for("showDecks", username=username, selecteddeckid=selectedDeck))


@app.route("/getRandomCard", methods=["GET"])
def getRandomCard():
    try:
        db = getDb()
        cursor = db.cursor()
        # Only select the fields we need
        cursor.execute("SELECT Name, Damage, Cost, Health FROM Cards ORDER BY RANDOM() LIMIT 1")
        card = cursor.fetchone()
        db.close()
        
        if card:
            return jsonify({
                "name": card[0],     # Name from DB
                "attack": card[1],    # Damage from DB
                "cost": card[2],      # Cost from DB
                "health": card[3]     # Health from DB
            })
        return jsonify({"error": "No card found"}), 404
    except Exception as e:
        print(f"Error getting random card: {e}")
        return jsonify({"error": str(e)}), 500


# -------- network testing ---------

@app.route("/networkTest", methods=["GET"])
def networkTest():
    return render_template("networkTest.html")


# @app.route("/networkTest/getGame", methods=["GET"])
# def getGame():
#     global globalGameCount
#     global globalGameList
#     dumpGlobalState()
#     if not session.get("Username"): 
#         return '{"status" : "please login before joining a game"}'  # Check if user is logged in
#     username = session.get("Username")
#     if session.get("CurrentGame"): 
#         return '{"status" : "in game"}'  # Check if user is already in a game
#     session["CurrentGame"] = globalGameCount
    
#     for game in globalGameList:
#         if game.player2 is None:
#             game.player2 = username  # Assign user to player2 if slot is empty
#             dumpGlobalState()
#             session.modified = True
#             return '{"isPlayer1" : false}'  # User is player2
            
#     globalGameCount += 1
#     newGame = Game(username, None, globalGameCount, 0, None)
#     newGame.player1.username = username  # Assign user to player1
#     globalGameList.append(newGame)
#     session["CurrentGame"] = globalGameCount
#     dumpGlobalState()
#     session.modified = True
#     return '{"isPlayer1" : true}'  # User is player1


# @app.route("/networkTest/waitForPlayer2", methods=["GET"])
# def waitForPlayer2():
#     global globalGameCount
#     global globalGameList
#     dumpGlobalState()
#     if session.get("CurrentGame"): 
#         game = globalGameList[(session["CurrentGame"] - 1)]
#         return '{"player2Found" :"' + str(game.player2) + '"}'  # Return player2's username
#     return '{"ERROR no current game" : true}'  # Error if no current game


# @app.route("/networkTest/login", methods=["POST"])
# def networkLogin():
#     username = request.form["Username"]
#     session["Username"] = username  # Store username in session
#     return '{"status" : "logged in"}'



def dumpGlobalState():
    global globalGameList
    global globalGameCount
    print("Global Game List")
    print(globalGameList)
    print("Global Game Count")
    print(globalGameCount)
    print("Session")
    if session.get("CurrentGame"):
        print("Found session:" + str(session["CurrentGame"]))
    else:
        print("No session")


def resetUserGameState(username):
    """Reset a user's game state so they can join new games."""
    session.pop("CurrentGame", None)
    session.pop("InGame", None)
    
    # Optionally: Clean up any abandoned games where this user was a player
    global globalGameList
    abandoned_games = [i for i, game in enumerate(globalGameList) 
                     if game.player1.username == username or game.player2.username == username]
    
    # Remove abandoned games (in reverse order to maintain indexes)
    for i in reversed(abandoned_games):
        globalGameList.pop(i)
        
    # Adjust game IDs
    for i, game in enumerate(globalGameList):
        game.gameId = i + 1
        
    global globalGameCount
    globalGameCount = len(globalGameList)
    
    # Save state
    dumpGlobalState()


# -------- miscellaneous ---------


@app.route("/test_alert/<alert_type>", methods=["POST"]) # test alert
def test_alert(alert_type):
    if alert_type == "info":
        flash("This is an info alert!", "info")
    elif alert_type == "success":
        flash("This is a success alert!", "success")
    elif alert_type == "error":
        flash("This is an error alert!", "error")
    return redirect(url_for("index"))


@app.route("/template")
def temp():
    if not session.get("Username"):  # check if the user is logged in
        return redirect(url_for("login"))
    profilePicPath = getProfilePicPath(session["Username"])  # get pfp
    username = session["Username"]  # get username

    return render_template("template.html", profile_pic=profilePicPath, username=username)



def runAttackSequence(game):
    # check whose turn it is
    player1sTurn = game.roundNum % 2 == 0
    # each attack card attacks in sequence the other players attack cards and then defence cards and then the player
    # while there are attack cards
    # take the next attacking card and try and attack the other player's attack cards, defence cards and then the player
    attacking_cards = game.gameBoard.p1Attack if player1sTurn else game.gameBoard.p2Attack
    defending_attack_cards = game.gameBoard.p2Attack if player1sTurn else game.gameBoard.p1Attack
    defending_defence_cards = game.gameBoard.p2Defence if player1sTurn else game.gameBoard.p1Defence
    defending_attack_card_index = 0
    defending_defence_card_index = 0
    for i in range(0, len(attacking_cards)):
        if defending_attack_card_index < len(defending_attack_cards):
            defending_attack_cards[defending_attack_card_index].health -= attacking_cards[i].attack 
            defending_attack_card_index += 1
        elif defending_defence_card_index < len(defending_defence_cards):
            defending_defence_cards[defending_defence_card_index].health -= attacking_cards[i].attack
            defending_defence_card_index += 1
        else:
            if player1sTurn:
                game.player2.health -= attacking_cards[i].attack
            else:
                game.player1.health -= attacking_cards[i].attack
#else:
    # placeholder for attacking the player
        #else:
            # placeholder for attacking the player
        #else:
            # placeholder for attacking the player
#else:
    # placeholder for attacking the player
        #else:
            # placeholder for attacking the player
        #else:
            # placeholder for attacking the player


# -------- flask --------

if __name__ == "__main__":
    globalGameCount = 0
    globalGameList = []
    app.run(debug=True)
