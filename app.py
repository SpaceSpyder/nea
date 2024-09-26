#pip install -U Flask
#pip install Jinja2
#pip install SQLAlchemy
#pip install Flask-SQLAlchemy
#pip install werkzeug

import sys
import os
from datetime import datetime, timedelta
import sqlite3  # Importing sqlite3 for database interactions
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from templates.scripts.utils import get_profile_pic_path,get_user_id_by_username,get_user_details_by_username,get_decks_for_user
sys.path.append(os.path.join(os.path.dirname(__file__), 'templates', 'scripts'))
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask import session, render_template
from templates.scripts.utils import get_profile_pic_path
from sqlalchemy.orm import Session

# Replace these with your actual database URI
DATABASE_URI = 'sqlite:///your_database.db'  # Example for SQLite
engine = create_engine(DATABASE_URI)

Session = sessionmaker(bind=engine)  # Create a session factory




hashed_password = generate_password_hash('admin')  # Replace 'admin' with the actual password
print(hashed_password)  # Copy this hashed password to your SQL command above

app = Flask(__name__, static_folder='templates', static_url_path='')
app.config['SECRET_KEY'] = 't67wtEq'
app.config['UPLOAD_FOLDER'] = os.path.join('templates', 'images', 'profilePics')  # Using os.path.join for path compatability


# Create the upload directory if it doesn't exist
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Define your database connection
DATABASE_URL = 'sqlite:///databases/database.db'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Session configuration
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)



@app.teardown_appcontext
def close_db(error):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()



@app.route('/decks')
@app.route('/profile/decks')
def show_decks():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if the user is not logged in

    username = session['username']
    user_id = get_user_id_by_username(username)
    decks = get_decks_for_user(user_id)
    return render_template('decks.html', decks=decks)


@app.route('/home')
@app.route('/index')
@app.route('/')
def index():
    username = session.get('username')
    
    session_db = Session()  # Create a session bound to the engine
    
    # Call the function directly
    full_profile_pic_path = get_profile_pic_path(username, session_db)

    # Close the session after usage
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
        return redirect(url_for('login'))  # Redirect to login if the user is not logged in
    return render_template('game.html')


@app.route('/testGame2')
def testGame2():
    return render_template('game2.html')

@app.route('/temp')
def temp():
    return render_template('temp.html')

@app.route('/dbTest')
def dbTest():
    conn = sqlite3.connect('databases/database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM Users')
    rows = cursor.fetchall()
    result = ", ".join(str(row) for row in rows)
    conn.close()
    return render_template('record.html', name=result)

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        print(f"Attempting to login with username: {username}")  # Debugging line

        query = text("SELECT * FROM Users WHERE Username = :username")
        session_db = Session()

        try:
            result = session_db.execute(query, {'username': username}).fetchone()
            print(f"Query result: {result}")  # Debugging line

            if result:
                hashed_password = result[2]  # Adjust based on your actual table structure
                print(f"Hashed password from DB: {hashed_password}")  # Debugging line
                
                if check_password_hash(hashed_password, password):
                    session['username'] = username
                    session.permanent = True
                    flash('Logged in successfully!', 'success')
                    return redirect(url_for('index'))
                else:
                    print("Password mismatch")  # Debugging line
                    flash('Incorrect username / password!', 'error')
            else:
                print("Username not found")  # Debugging line
                flash('Incorrect username / password!', 'error')
        except Exception as e:
            print(f"Error: {e}")  # Debugging line
            flash('An error occurred. Please try again.', 'error')
        finally:
            session_db.close()

    return render_template('login.html')



@app.route('/signUp', methods=['GET', 'POST'])
def signUp():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])  # Hash the password
        email = request.form['email']
        date = datetime.today().strftime('%Y-%m-%d')

        query = text("""INSERT INTO Users (Username, Password, Email, DateCreated)
                        VALUES (:username, :password, :email, :date)""")
        
        session_db = Session()
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

    return render_template('signUp.html')

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
    
    # Get the current database session
    session_db = Session()

    # Call the function with both parameters
    full_profile_pic_path = get_profile_pic_path(username, session_db)

    session_db.close()  # Close the session after use

    return render_template('profile.html', profile_pic=full_profile_pic_path)

@app.route('/profile/changePfp', methods=['GET', 'POST'])
def change_profile_pic():
    # Initialize the variable
    full_profile_pic_path = url_for('static', filename='images/profilePics/Default.png')  # Default picture

    # Retrieve the logged-in user's username
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect if not logged in

    username = session['username']
    
    # Get user details from the database
    user_details = get_user_details_by_username(username)

    # Check if user details are found
    if user_details:
        user_id, profile_pic = user_details
        full_profile_pic_path = url_for('static', filename=f'images/profilePics/{profile_pic}') if profile_pic else url_for('static', filename='images/profilePics/Default.png')
    else:
        full_profile_pic_path = url_for('static', filename='images/profilePics/Default.png')

    print("Change Profile Picture Path: ", full_profile_pic_path)  # Debug statement

    # Check if the request method is POST
    if request.method == 'POST':
        # Check if a file was uploaded
        if 'profile_pic' not in request.files:
            flash('No file part', 'error')  # Flash an error message if no file
            return redirect(url_for('profile'))

        file = request.files['profile_pic']
        # Ensure a file was selected
        if file.filename == '':
            flash('No selected file', 'error')  # Flash an error message if no file selected
            return redirect(url_for('profile'))

        if file:
            # Use secure_filename to prevent issues with filename
            filename = secure_filename(file.filename)
            # Save the file to the specified upload folder
            app.config['UPLOAD_FOLDER'] = os.path.join('templates', 'images', 'profilePics')

            # Create the upload directory if it doesn't exist
            if not os.path.exists(app.config['UPLOAD_FOLDER']):
                os.makedirs(app.config['UPLOAD_FOLDER'])

            # When saving a file
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # Update the user's profile picture in the database
            query = text("UPDATE Users SET ProfilePicture = :profile_pic WHERE Username = :username")
            session_db = Session()
            try:
                # Ensure the filename stored is just the name, not the entire path
                session_db.execute(query, {'profile_pic': filename, 'username': username})
                session_db.commit()
                flash('Profile picture updated successfully!', 'success')
            except Exception as e:
                session_db.rollback()
                flash(f'Error: {str(e)}', 'error')
            finally:
                session_db.close()

            return redirect(url_for('profile'))  # Redirect to the profile page after update

    # Render the template on GET request, showing the current profile picture
    return render_template('changePfp.html', profile_pic=full_profile_pic_path)


@app.route('/use_deck', methods=['POST'])
def use_deck():
    if 'username' not in session:
        return redirect(url_for('login'))  # Redirect to login if the user is not logged in

    selected_deck = request.form.get('decks')  # Changed to 'decks' to match the select name in HTML
    flash(f'You are now using the deck: {selected_deck}', 'success')
    return redirect(url_for('testGame'))  # Redirect to the game

if __name__ == '__main__':
    app.run(debug=True)
