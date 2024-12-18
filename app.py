from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os  # Import os module
import json  # Import json module

from templates.scripts.utils import (
    getProfilePicPath,
    getUserIdByUsername,
    getUserDetailsByUsername,
    getDecksForUser,
    getDeckForUser,
    getDb,
    closeDb,
    checkUsername,
    calculateRank,
)

# Database setup
DATABASE_URI = "databases/database.db"  # SQLite database file path
DEFAULT_PIC_PATH = "images/profilePics/Default.png"

# Flask app setup
app = Flask(__name__, static_folder="templates", static_url_path="")
app.config["SECRET_KEY"] = "t67wtEq"
app.config["UPLOAD_FOLDER"] = os.path.join("templates", "images", "profilePics")
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=1)  # session timeout after 1 hour


@app.route("/home")
@app.route("/index")
@app.route("/")
def index():
    username = session.get("Username")
    profile_pic_path = getProfilePicPath(username) if username else getProfilePicPath()
    return render_template("index.html", profile_pic=profile_pic_path)


@app.route("/login", methods=["POST", "GET"])
def login():
    profile_pic_path = getProfilePicPath()  # get pfp

    # Check if the user is already logged in
    if "Username" in session:
        flash("You are already logged in!", "info")
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = getDb()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE Username = ?", (username,))
        result = cursor.fetchone()
        if result and check_password_hash(result[2], password):  # Adjust based on your actual table structure
            getUserDetailsByUsername(username)
            flash("Logged in successfully!", "success")
            return redirect(url_for("index"))
        else:
            flash("Incorrect username / password!", "error")

    return render_template("login.html",profile_pic=profile_pic_path)


@app.route("/signUp", methods=["GET", "POST"])
def signUp():
    if "Username" in session:
        flash("You are already signed up!", "info")
        return redirect(url_for("index"))

    profile_pic_path = getProfilePicPath()  # Default profile picture path

    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        email = request.form["email"]

        try:
            insert_user(username, password, email)
            session["Username"] = username
            session.permanent = True
            flash("Signed up successfully!", "success")
            return redirect(url_for("index"))
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: Users.Username" in str(e):
                flash("Username already exists. Please choose a different username.", "error")
            else:
                flash(f"Error: {str(e)}", "error")
            return render_template("signUp.html", profile_pic=profile_pic_path)

    return render_template("signUp.html", profile_pic=profile_pic_path)


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


@app.route("/profile")
def profile():
    if not session.get("Username"):
        return redirect(url_for("login"))
    profile_pic_path = getProfilePicPath(session["Username"])

    return render_template("profile.html", profile_pic=profile_pic_path)


@app.route("/profile/stats", methods=["GET"])
@app.route("/stats", methods=["GET"])
@app.route("/profile/stats/<username>", methods=["GET"])
@app.route("/stats/<username>", methods=["GET"])
def stats(username=None):
    if not session.get("Username"):  # check if the user is logged in
        return redirect(url_for("login"))
    
    # If username is not provided in the URL, use the logged-in user's username
    if username is None:
        username = session["Username"]

    account_pic_path = getProfilePicPath(username)
    profile_pic_path = getProfilePicPath(session["Username"])  # get pfp for the username (either from URL or session)
    session_username = session["Username"]  # get logged-in user's username

    conn = getDb()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT Id FROM Users WHERE Username = ?", (username,))
        result = cursor.fetchone()

        if result:
            user_id = result[0]
            cursor.execute("SELECT GamesPlayed, GamesWon, DateCreated, FavouriteCard FROM UserStats WHERE UserId = ?", (user_id,))
            user_stats = cursor.fetchone()

            if user_stats:
                rank = calculateRank(username)  # Calculate the rank
                stats_data = {
                    "Rank": rank,
                    "GamesPlayed": user_stats[0],
                    "GamesWon": user_stats[1],
                    "DateCreated": user_stats[2],
                    "FavouriteCard": user_stats[3]
                }
            else:
                stats_data = {"Rank": "N/A", "GamesPlayed": 0, "GamesWon": 0, "DateCreated": "N/A", "FavouriteCard": "N/A"}
        else:
            stats_data = {"Rank": "N/A", "GamesPlayed": 0, "GamesWon": 0, "DateCreated": "N/A", "FavouriteCard": "N/A"}
    finally:
        cursor.close()

    return render_template("stats.html", profile_pic=profile_pic_path, stats=stats_data, username=session_username, account_pic=account_pic_path)



@app.route("/decks/<username>", methods=["GET", "POST"])
@app.route("/profile/decks/<username>", methods=["GET", "POST"])
def show_decks(username):
    if not session.get("Username"):  # check if the user is logged in
        return redirect(url_for("login"))
    profile_pic_path = getProfilePicPath(session["Username"])  # get pfp
    session_username = session["Username"]  # get username

    # Check if the user exists
    user_id = getUserIdByUsername(username)
    if not user_id:
        flash("User not found", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        selected_cards = request.form.get("selectedCards")
        if selected_cards:
            selected_cards = json.loads(selected_cards)
            # Add your logic for creating a new deck with the selected cards here
            flash("New deck created successfully!", "success")
            return redirect(url_for("show_decks", username=username))

    # Get deck ID from URL parameters, if any
    deck_id = request.args.get("deck", session.get("CurrentDeck"))

    # Retrieve decks for the specified username
    decks = getDecksForUser(username)
    deck = getDeckForUser(username, deck_id)

    # Fetch the current deck from the database
    try:
        conn = sqlite3.connect("databases/database.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Deck FROM Decks
            WHERE Owner = ?
        """, (username,))
        deck_row = cursor.fetchone()
        current_deck = deck_row[0].split(", ") if deck_row else []
    except sqlite3.Error as e:
        flash(f"Error: {str(e)}", "error")
        current_deck = []
    finally:
        cursor.close()
        conn.close()

    return render_template(
        "decks.html",
        profile_pic=profile_pic_path,
        username=session_username,
        decks=decks,
        deck=deck,
        current_deck=current_deck
    )


@app.route("/profile/changePfp", methods=["GET", "POST"])
def change_profile_pic():
    if not session.get("Username"):  # check if the user is logged in
        return redirect(url_for("login"))
    profile_pic_path = getProfilePicPath(session["Username"])  # get pfp
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

            return redirect(url_for("profile"))

    # Render the change profile picture template
    return render_template("changePfp.html", profile_pic=profile_pic_path)


@app.route("/use_deck", methods=["POST"])
def use_deck():
    if not session.get("Username"):  # check if the user is logged in
        return redirect(url_for("login"))
    profile_pic_path = getProfilePicPath(session["Username"])  # get pfp
    username = session["Username"]  # get username

    selected_deck = request.form.get("decks")
    flash(f"You are now using the deck: {selected_deck}", "success")
    return redirect(url_for("testGame"))


@app.route("/submit", methods=["GET", "POST"])
def submit():
    if request.method == "POST":
        userinput = request.form["user_input"]
        return f"You entered: {userinput}"
    else:
        return "ERROR Method Not Allowed"


@app.route("/testGame")
def testGame():
    # Check if the user is logged in
    username = checkUsername()
    if username:
        profile_pic_path = getProfilePicPath(username)  # get profile picture path from the user details
        return render_template("game.html", profile_pic=profile_pic_path)
    else:
        return redirect(url_for("login"))  # Redirect response if the user is not logged in
    

@app.route("/dbTest", methods=["GET"])
def dbTest():
    username = session.get("Username")
    full_profile_pic_path = getProfilePicPath()

    conn = getDb()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Users")
    rows = cursor.fetchall()
    result = ", ".join(str(row) for row in rows)
    return render_template("record.html", name=result, profile_pic=full_profile_pic_path)


def insert_user(username, password, email):
    date = datetime.today().strftime("%Y-%m-%d")
    conn = getDb()
    cursor = conn.cursor()
    try:
        with conn:
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
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")  # Error handling
        raise
    finally:
        cursor.close()
        closeDb(conn)  # Close the database connection


@app.route("/create_deck/<username>", methods=["POST"])
def create_deck(username):
    if not session.get("Username"):  # check if the user is logged in
        return redirect(url_for("login"))

    selected_cards = request.form.get("selectedCards")
    if selected_cards:
        # Add your logic for creating a new deck with the selected cards here
        # For example, insert the selected cards into the database
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
                    INSERT INTO Decks (Owner, UserDeckNum, Deck)
                    VALUES (?, ?, ?)
                """, (username, user_deck_num, selected_cards))
                flash("New deck created successfully!", "success")
        except sqlite3.Error as e:
            flash(f"Error: {str(e)}", "error")
        finally:
            cursor.close()

    return redirect(url_for("show_decks", username=username))


@app.route("/template")
def temp():
    if not session.get("Username"):  # check if the user is logged in
        return redirect(url_for("login"))
    profile_pic_path = getProfilePicPath(session["Username"])  # get pfp
    username = session["Username"]  # get username

    return render_template("template.html", profile_pic=profile_pic_path)


@app.route("/test_alert/<alert_type>", methods=["POST"])
def test_alert(alert_type):
    if alert_type == "info":
        flash("This is an info alert!", "info")
    elif alert_type == "success":
        flash("This is a success alert!", "success")
    elif alert_type == "error":
        flash("This is an error alert!", "error")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=False)
