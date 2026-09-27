# For user log-in

from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_here'

USER_DATABASE = {
    "admin_user": generate_password_hash("securepassword123")
}

@app.route('/')
def home():
    return 'Welcome to the homepage of The Bard! <a href="/login">Sign In here</a>.'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form.get('username')
        pw = request.form.get('password')

        if user in USER_DATABASE:
            hashed_password = USER_DATABASE[user]

            if check_password_hash(hashed_password, pw):
                return f"Welcome back, {user}! Sign-in successful."

        flash("Incorrect usename or password. Please try again.")
        return redirect(url_for('login'))
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug = True)