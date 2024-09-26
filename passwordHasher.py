import sqlite3
from werkzeug.security import generate_password_hash

def update_user_password(username, new_password):
    # Connect to the SQLite database
    conn = sqlite3.connect('databases/database.db')
    cursor = conn.cursor()

    # Hash the new password
    hashed_password = generate_password_hash(new_password)

    # Update the password in the database
    cursor.execute("UPDATE Users SET Password = ? WHERE Username = ?", (hashed_password, username))
    
    # Commit the changes and close the connection
    conn.commit()
    conn.close()

# Usage example
update_user_password('admin', 'admin')
