'''pip install -U Flask
pip install Jinja2
pip install SQLAlchemy
pip install Flask SQLAlchemy'''

import sqlite3
from flask import Flask, render_template, request, redirect, url_for, make_response, flash, session
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime


app = Flask(__name__, static_folder='templates', static_url_path='')
app.config['SECRET_KEY'] = 't67wtEq'

# Define your database connection
DATABASE_URL = 'sqlite:///databases/database.db'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

flash('Logged in successfully!', 'success')
flash('Signed up successfully!', 'success')
flash('You have been logged out.', 'success')

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect('database.db')
    return db

@app.route('/decks')
def show_decks():
    # Assuming you have a way to get the logged-in user's ID
    user_id = 1  # Replace with actual user ID from session or authentication
    decks = get_decks_for_user(user_id)
    return render_template('decks.html', decks=decks)

def get_decks_for_user(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT Deck, UserDeckNum FROM decks WHERE Owner = ?", (user_id,))
    return cursor.fetchall()

@app.teardown_appcontext
def close_db(error):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/index')
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['GET', 'POST'])  # Assign webpage name and methods to use
def submit():
    if request.method == 'POST':
        user_input = request.form['user_input']
        return f'You entered: {user_input}'
    else:
        return 'ERROR Method Not Allowed'

@app.route('/testGame')
def testGame():
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

    # Create a cursor object
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM Users')

    # Fetch all rows from the executed query
    rows = cursor.fetchall()

    # Iterate over the rows and print each one
    result = ""
    for row in rows:
        result += ", " + str(row)

    conn.close()

    return render_template('record.html', name=result)

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']  # Gets username and password entered on webpage
        password = request.form['password']

        # Query to check if the user exists
        query = text("SELECT * FROM Users WHERE username = :username AND password = :password")
        with Session() as session:
            result = session.execute(query, {'username': username, 'password': password}).fetchone()

        if result:
            msg = 'Logged in successfully!'
            response = make_response(redirect(url_for('index')))
            response.set_cookie('username', username, max_age=3600)
            return response
        else:
            msg = 'Incorrect username / password!'
            return render_template('login.html', msg=msg)

    return render_template('login.html')

@app.route('/signUp', methods=['GET', 'POST'])
def signUp():
    if request.method == 'POST':
        username = request.form['username']  # Gets username, password, and email entered on webpage
        password = request.form['password']
        email = request.form['email']
        date = datetime.today().strftime('%Y-%m-%d')

        # Insert query with placeholders
        query = text("""INSERT INTO Users (Username, Password, Email, DateCreated)
                        VALUES (:username, :password, :email, :date)""")

        try:
            with Session() as session:
                # Execute the query and commit
                session.execute(query, {'username': username, 'password': password, 'email': email, 'date': date})
                session.commit()  # Save the changes

            # Successful insertion, log in the user
            msg = 'Signed up successfully!'
            response = make_response(redirect(url_for('index')))
            response.set_cookie('username', username, max_age=3600)
            return response

        except Exception as e:
            # Handle any errors (e.g., database issues)
            msg = f'Error: {str(e)}'
            return render_template('signUp.html', msg=msg)

    # If not POST, render the sign-up page
    return render_template('signUp.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

if __name__ == '__main__':
    app.run(debug=True)
