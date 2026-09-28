import sqlite3
from werkzeug.security import generate_password_hash

connection = sqlite3.connect("website.db")
cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT UNIQUE NOT NULL,
password TEXT NOT NULL)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS favorites (
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER NOT NULL,
post_id INTEGER NOT NULL,
FOREIGN KEY (user_id) REFERENCES users(id)
)""")

cursor.execute(
    "INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
    ("admin_user", generate_password_hash("securepassword123"))
)

connection.commit()
connection.close()

print("Database created successfully")