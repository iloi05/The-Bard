from flask import Flask, render_template

app = Flask(__name__)

artists = [
    {
        "name": "Artist 1",
        "image": "The bard images/placeholder.png",
        "information": "Artist information here"
    },
    {
        "name": "Artist 2",
        "image": "The bard images/placeholder.png",
        "information": "Artist information here"
    },
    {
        "name": "Artist 3",
        "image": "The bard images/placeholder.png",
        "information": "Artist information here"
    },
    {
        "name": "Artist 4",
        "image": "The bard images/placeholder.png",
        "information": "Artist information here"
    }
]

@app.route("/")
def home():
    return render_template("home.html", artists=artists)