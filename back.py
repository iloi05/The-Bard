# For user log-in

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here'

artists = [
    {
        "id": 1,
        "name": "Artist 1",
        "image": "The bard images/placeholder.png",
        "information": "Artist information here"
    },
    {
        "id": 2,
        "name": "Artist 2",
        "image": "The bard images/placeholder.png",
        "information": "Artist information here"
    },
    {
        "id": 3,
        "name": "Artist 3",
        "image": "The bard images/placeholder.png",
        "information": "Artist information here"
    },
    {
        "id": 4,
        "name": "Artist 4",
        "image": "The bard images/placeholder.png",
        "information": "Artist information here"
    }
]

USER_DATABASE = {
    "admin_user": generate_password_hash("securepassword123")
}

@app.route("/")
def home():
    return render_template("home.html", artists=artists)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username')
        pw = request.form.get('password')

        connection = sqlite3.connect("website.db")
        cursor = connection.cursor()

        cursor.execute(
            "SELECT id, password FROM users WHERE username = ?",
            (user,)
        )

        account = cursor.fetchone()
        connection.close()

        if account is not None:
            user_id, hashed_password = account

            if check_password_hash(hashed_password, pw):
                session["uid"] = user_id
                return redirect(url_for("home"))

        flash("Incorrect usename or password. Please try again.")
        return redirect(url_for('login'))
    return render_template('login.html')

#@app.route("/favorite/<int:post_id>", methods=["POST"])
#def favorites(post_id):
#    uid = session.get("uid")
#
#    if uid is None:
#        return redirect(url_for("login"))
#
#    connection = sqlite3.connect("website.db")
#    cursor = connection.cursor()
#
#    cursor.execute(
#        "INSERT INTO favorites (user_id, post_id) VALUES (?, ?)",
#        (uid, post_id)
#    )
#    connection.commit()
#    connection.close()
#
#    return redirect(url_for("home"))

@app.route("/favorites")
def favorites_page():
    #uid = session.get("uid")
#
    #if uid is None:
    #    return redirect(url_for("login"))
    return render_template("fav.html", artists = artists)

if __name__ == '__main__':
    app.run(debug = True)