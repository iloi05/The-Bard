# Install flask so this can work for both of us
# use flask run when you want to run the file
from flask import Flask, session, redirect, url_for
import sqlite3

app = Flask(__name__)
app.secret_key = "secret-key"

@app.route('/favorite/<int:post_id>', methods=['POST'])

def favorites(post_id):
    uid = session.get("uid")
    if uid is None:
        return redirect(url_for("login"))

    connection = sqlite3.connect("website.db")
    cursor = connection.cursor()

    cursor.execute(
        "INSERT INTO favorites (user_id, post_id) VALUES (?, ?)",
        (uid, post_id)
    )

    connection.commit()
    connection.close()

    return redirect(url_for("some_page"))