from flask import Flask, render_template

app = Flask(__name__)

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

@app.route("/")
def home():
    return render_template("home.html", artists=artists)

@app.route("/favorites")
def favorites_page():
    return render_template("fav.html", artists = artists)

if __name__ == '__main__':
    app.run(debug = True)