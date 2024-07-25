'''pip install -U Flask
pip install Jinja2
pip install SQLAlchemy
pip install Flask SQLAlchemy'''


import sqlite3
from flask import Flask, render_template, request, redirect, url_for, make_response
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker


app = Flask(__name__, static_folder='templates', static_url_path='')
app.config['SECRET_KEY'] = 't67wteq'  

# Define your database connection
DATABASE_URL = 'sqlite:///databases/database.db'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


@app.route('/index')
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['GET', 'POST']) # assign webpage name and methods to use
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
        result+=", " + str(row)

    conn.close()

    return render_template('record.html', name=result)



@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username'] # gets username and pw entered on webpage
        password = request.form['password']

        # no idea how this part works lol
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


@app.route('/signUp')
def signUp():

    return render_template('signUp.html')








if __name__ == '__main__':
    app.run(debug=True)