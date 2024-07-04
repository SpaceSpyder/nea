#pip install -U Flask
#pip install Jinja2

import sqlite3
from flask import Flask, render_template
from flask import request

app = Flask(__name__, static_folder='templates', static_url_path='')

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

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signUp')
def signUp():
    return render_template('signUp.html')

@app.route('/dbTest')
def dbTest():
    conn = sqlite3.connect('databases/database.db')

    # Create a cursor object
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users')

    # Fetch all rows from the executed query
    rows = cursor.fetchall()

    # Iterate over the rows and print each one
    result = ""
    for row in rows:
        result+=", " + str(row)

    conn.close()

    return render_template('record.html', name=result)

@app.route('/loggingin', methods=['POST'])
def loggingin():
    # Select data from the database for the requested username and password
    # check if the result shows a match
    # if no match tell the user
    # e.g. render template YOUOLOGGEDIN.html
    # else
    # set a cookie with the users name and database id
    # render template game.html and load their deck (or new)

    return ""
   








if __name__ == '__main__':
    app.run(debug=True)