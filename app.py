# Required Libraries
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from templates.scripts.models import Users, Decks  # Import your models
from templates.scripts.utils import (
    get_profile_pic_path,
    get_user_id_by_username,
    get_user_details_by_username,
    get_decks_for_user,
)

# Database setup
DATABASE_URI = 'sqlite:///databases/database.db'  # SQLite database URI
engine = create_engine(DATABASE_URI)
SessionLocal = sessionmaker(bind=engine)

# Flask app setup
app = Flask(__name__, static_folder='templates', static_url_path='')
app.config['SECRET_KEY'] = 't67wtEq'
app.config['UPLOAD_FOLDER'] = os.path.join('templates', 'images', 'profilePics')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)

# Helper function to create a new session
def get_session():
    return SessionLocal()

@app.route('/decks', methods=['GET', 'POST'])
@app.route('/profile/decks', methods=['GET', 'POST'])
def show_decks():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    session_db = get_session()  # Create a session bound to the engine
    try:
        full_profile_pic_path = get_profile_pic_path(username, session_db)
        user_id = get_user_id_by_username(username)
        decks = get_decks_for_user(user_id, session_db)

        if request.method == 'POST':
            selected_deck = request.form['options']
            flash(f'You selected: {selected_deck}', 'success')
            # Handle the selected deck as needed (e.g., redirect or process further)

    finally:
        session_db.close()  # Ensure the session is closed

    return render_template('decks.html', decks=decks, profile_pic=full_profile_pic_path)



@app.route('/home')
@app.route('/index')
@app.route('/')
def index():
    username = session.get('username')
    session_db = get_session()
    full_profile_pic_path = get_profile_pic_path(username, session_db)
    session_db.close()
    return render_template('index.html', profile_pic=full_profile_pic_path)

@app.route('/submit', methods=['GET', 'POST'])
def submit():
    if request.method == 'POST':
        user_input = request.form['user_input']
        return f'You entered: {user_input}'
    else:
        return 'ERROR Method Not Allowed'

@app.route('/testGame')
def testGame():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('game.html')

@app.route('/testGame2')
def testGame2():
    return render_template('game2.html')

@app.route('/temp')
def temp():
    return render_template('temp.html')

@app.route('/dbTest', methods=['GET'])
def dbTest():
    username = session.get('username')
    session_db = get_session()
    full_profile_pic_path = get_profile_pic_path(username, session_db)
    session_db.close()

    conn = get_session().bind.raw_connection()  # Use SQLAlchemy's connection
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Users')
    rows = cursor.fetchall()
    result = ", ".join(str(row) for row in rows)
    conn.close()
    return render_template('record.html', name=result, profile_pic=full_profile_pic_path)

@app.route('/login', methods=['POST', 'GET'])
def login():
    username = session.get('username')
    session_db = get_session()
    full_profile_pic_path = get_profile_pic_path(username, session_db)

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        query = text("SELECT * FROM Users WHERE Username = :username")
        try:
            result = session_db.execute(query, {'username': username}).fetchone()
            if result and check_password_hash(result[2], password):  # Adjust based on your actual table structure
                session['username'] = username
                session.permanent = True
                flash('Logged in successfully!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Incorrect username / password!', 'error')
        except Exception as e:
            flash(f'An error occurred: {str(e)}', 'error')
        finally:
            session_db.close()

    return render_template('login.html', profile_pic=full_profile_pic_path)

@app.route('/signUp', methods=['GET', 'POST'])
def signUp():
    username = session.get('username')
    session_db = get_session()
    full_profile_pic_path = get_profile_pic_path(username, session_db)

    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        email = request.form['email']
        date = datetime.today().strftime('%Y-%m-%d')

        query = text("""INSERT INTO Users (Username, Password, Email, DateCreated)
                        VALUES (:username, :password, :email, :date)""")

        session_db = get_session()
        try:
            session_db.execute(query, {'username': username, 'password': password, 'email': email, 'date': date})
            session_db.commit()
            session['username'] = username
            session.permanent = True
            flash('Signed up successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            session_db.rollback()
            flash(f'Error: {str(e)}', 'error')
            return render_template('signUp.html')
        finally:
            session_db.close()

    return render_template('signUp.html', profile_pic=full_profile_pic_path)

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    session_db = get_session()
    full_profile_pic_path = get_profile_pic_path(username, session_db)
    session_db.close()

    return render_template('profile.html', profile_pic=full_profile_pic_path)

@app.route('/profile/changePfp', methods=['GET', 'POST'])
def change_profile_pic():
    full_profile_pic_path = url_for('static', filename='images/profilePics/Default.png')

    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    user_details = get_user_details_by_username(username)

    if user_details:
        user_id, profile_pic = user_details
        full_profile_pic_path = url_for('static', filename=f'images/profilePics/{profile_pic}') if profile_pic else full_profile_pic_path

    if request.method == 'POST':
        if 'profile_pic' not in request.files:
            flash('No file part', 'error')
            return redirect(url_for('profile'))

        file = request.files['profile_pic']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(url_for('profile'))

        if file:
            filename = secure_filename(file.filename)
            app.config['UPLOAD_FOLDER'] = os.path.join('templates', 'images', 'profilePics')

            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])

            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            query = text("UPDATE Users SET ProfilePicture = :profile_pic WHERE Username = :username")
            session_db = get_session()
            try:
                session_db.execute(query, {'profile_pic': filename, 'username': username})
                session_db.commit()
                flash('Profile picture updated successfully!', 'success')
            except Exception as e:
                session_db.rollback()
                flash(f'Error: {str(e)}', 'error')
            finally:
                session_db.close()

            return redirect(url_for('profile'))

    return render_template('changePfp.html', profile_pic=full_profile_pic_path)

@app.route('/use_deck', methods=['POST'])
def use_deck():
    if 'username' not in session:
        return redirect(url_for('login'))

    selected_deck = request.form.get('decks')
    flash(f'You are now using the deck: {selected_deck}', 'success')
    return redirect(url_for('testGame'))

@app.route('/profile/stats', methods=['GET'])
@app.route('/stats', methods=['GET'])
def stats():
    username = session.get('username')

    if not username:
        return "User not logged in", 403

    session_db = get_session()
    full_profile_pic_path = get_profile_pic_path(username, session_db)
    session_db.close()

    conn = get_session().bind.raw_connection()  # Use SQLAlchemy's connection
    cursor = conn.cursor()

    cursor.execute("SELECT Id FROM Users WHERE Username = ?", (username,))
    result = cursor.fetchone()

    if result:
        user_id = result[0]
        cursor.execute("SELECT GamesPlayed, GamesWon, DateCreated FROM UserStats WHERE UserId = ?", (user_id,))
        user_stats = cursor.fetchone()

        if user_stats:
            stats_data = {
                "GamesPlayed": user_stats[0],
                "GamesWon": user_stats[1],
                "DateCreated": user_stats[2]
            }
        else:
            stats_data = {"GamesPlayed": 0, "GamesWon": 0, "DateCreated": "N/A"}
    else:
        stats_data = {"GamesPlayed": 0, "GamesWon": 0, "DateCreated": "N/A"}

    cursor.close()
    conn.close()

    return render_template('stats.html', profile_pic=full_profile_pic_path, stats=stats_data)

if __name__ == '__main__':
    app.run(debug=True)
