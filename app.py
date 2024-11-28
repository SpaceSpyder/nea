from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os  # Import os module

from templates.scripts.utils import (
    get_profile_pic_path,
    get_user_id_by_username,
    get_user_details_by_username,
    get_decks_for_user,
    get_deck_for_user,
    get_db,
    close_db,
    check_username,
    calculate_rank,
)

# Database setup
DATABASE_URI = 'databases/database.db'  # SQLite database file path

# Flask app setup
app = Flask(__name__, static_folder='templates', static_url_path='')
app.config['SECRET_KEY'] = 't67wtEq'
app.config['UPLOAD_FOLDER'] = os.path.join('templates', 'images', 'profilePics')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)  # session timeout after 1 hour


@app.route('/home')
@app.route('/index')
@app.route('/')
def index():
    username = session.get('Username')
    profile_pic_path = get_profile_pic_path(username) if username else get_profile_pic_path()  # get profile picture path from the user details
    return render_template('index.html', profile_pic=profile_pic_path)


@app.route('/login', methods=['POST', 'GET'])
def login():
    # Check if the user is already logged in
    if 'Username' in session:
        flash('You are already logged in!', 'info')
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE Username = ?", (username,))
        result = cursor.fetchone()
        if result and check_password_hash(result[2], password):  # Adjust based on your actual table structure
            get_user_details_by_username(username)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Incorrect username / password!', 'error')

    return render_template('login.html')


@app.route('/signUp', methods=['GET', 'POST'])
def signUp():
    if 'Username' in session:
        flash('You are already signed up!', 'info')
        return redirect(url_for('index'))

    profile_pic_path = get_profile_pic_path()  # Default profile picture path

    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        email = request.form['email']

        try:
            insert_user(username, password, email)
            session['Username'] = username
            session.permanent = True
            flash('Signed up successfully!', 'success')
            return redirect(url_for('index'))
        except sqlite3.IntegrityError as e:
            if 'UNIQUE constraint failed: Users.Username' in str(e):
                flash('Username already exists. Please choose a different username.', 'error')
            else:
                flash(f'Error: {str(e)}', 'error')
            return render_template('signUp.html', profile_pic=profile_pic_path)

    return render_template('signUp.html', profile_pic=profile_pic_path)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))


@app.route('/profile')
def profile():
    if not session.get('Username'):
        return redirect(url_for('login'))
    profile_pic_path = get_profile_pic_path(session['Username'])

    return render_template('profile.html', profile_pic=profile_pic_path)


@app.route('/profile/stats', methods=['GET'])
@app.route('/stats', methods=['GET'])
def stats():
    if not session.get('Username'):  # check if the user is logged in
        return redirect(url_for('login'))
    profile_pic_path = get_profile_pic_path(session['Username'])  # get pfp
    username = session['Username']  # get username

    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT Id FROM Users WHERE Username = ?", (username,))
        result = cursor.fetchone()

        if result:
            user_id = result[0]
            cursor.execute("SELECT GamesPlayed, GamesWon, DateCreated, FavouriteCard FROM UserStats WHERE UserId = ?", (user_id,))
            user_stats = cursor.fetchone()

            if user_stats:
                rank = calculate_rank(username)  # Calculate the rank
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

    return render_template('stats.html', profile_pic=profile_pic_path, stats=stats_data, username=username)


@app.route('/decks/<username>', methods=['GET', 'POST'])
@app.route('/profile/decks/<username>', methods=['GET', 'POST'])
def show_decks(username):
    if not session.get('Username'): # check if the user is logged in
        return redirect(url_for('login'))
    profile_pic_path = get_profile_pic_path(session['Username']) # get pfp
    username = session['Username'] # get username

    
    # Check if the user exists
    user_id = get_user_id_by_username(username)
    if not user_id:
        flash('User not found', 'error')
        return redirect(url_for('index'))

    # Get deck ID from URL parameters, if any
    deck_id = request.args.get('deck', session.get('CurrentDeck'))

    # Retrieve decks for the specified username
    decks = get_decks_for_user(username)
    deck = get_deck_for_user(username, deck_id)

    return render_template(
        'decks.html', 
        username=username, 
        decks=decks, 
        deck=deck, 
        profile_pic=profile_pic_path
    )


@app.route('/profile/changePfp', methods=['GET', 'POST'])
def change_profile_pic():
    if not session.get('Username'): # check if the user is logged in
        return redirect(url_for('login'))
    profile_pic_path = get_profile_pic_path(session['Username']) # get pfp
    username = session['Username'] # get username

    # Handle the POST request to change the profile picture
    if request.method == 'POST':
        # Check if the profile picture file is in the request
        if 'profile_pic' not in request.files:
            flash('No file part', 'error')
            return redirect(url_for('profile'))

        file = request.files['profile_pic']
        # Check if a file is selected
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(url_for('profile'))

        if file:
            # Secure the filename and set the upload folder
            filename = secure_filename(file.filename)
            app.config['UPLOAD_FOLDER'] = os.path.join('templates', 'images', 'profilePics')

            # Create the upload folder if it doesn't exist
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])

            # Save the file to the upload folder
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Update the user's profile picture in the database
            conn = get_db()
            cursor = conn.cursor()
            try:
                cursor.execute("UPDATE Users SET ProfilePicture = ? WHERE Username = ?", (filename, username))
                conn.commit()
                flash('Profile picture updated successfully!', 'success')
            except sqlite3.Error as e:
                conn.rollback()
                flash(f'Error: {str(e)}', 'error')

            return redirect(url_for('profile'))

    # Render the change profile picture template
    return render_template('changePfp.html', profile_pic=profile_pic_path)


@app.route('/use_deck', methods=['POST'])
def use_deck():
    if not session.get('Username'): # check if the user is logged in
        return redirect(url_for('login'))
    profile_pic_path = get_profile_pic_path(session['Username']) # get pfp
    username = session['Username'] # get username

    selected_deck = request.form.get('decks')
    flash(f'You are now using the deck: {selected_deck}', 'success')
    return redirect(url_for('testGame'))


@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        user_input = request.form['user_input']
        return f'You entered: {user_input}'
    else:
        return 'ERROR Method Not Allowed'


@app.route('/testGame')
def testGame():
    username = check_username()  # Check if the user is logged in
    profile_pic_path = get_profile_pic_path(username)  # get profile picture path from the user details

    return render_template('game.html')


@app.route('/dbTest', methods=['GET'])
def dbTest():
    username = session.get('Username')
    full_profile_pic_path = get_profile_pic_path()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Users')
    rows = cursor.fetchall()
    result = ", ".join(str(row) for row in rows)
    return render_template('record.html', name=result, profile_pic=full_profile_pic_path)


def insert_user(username, password, email):
    date = datetime.today().strftime('%Y-%m-%d')
    conn = get_db()
    try:
        with conn:
            conn.execute("""INSERT INTO Users (Username, Password, Email, DateCreated, ProfilePicture)
                            VALUES (?, ?, ?, ?, 'Default.png')""",
                         (username, password, email, date))
    except sqlite3.OperationalError as e:
        print(f"Error: {e}")  # Error handling
        raise
    finally:
        close_db(conn)  # Close the database connection


@app.route('/template')
def temp():
    if not session.get('Username'): # check if the user is logged in
        return redirect(url_for('login'))
    profile_pic_path = get_profile_pic_path(session['Username']) # get pfp
    username = session['Username'] # get username

    return render_template('template.html', profile_pic=profile_pic_path)


if __name__ == '__main__':
    app.run(debug=True)
