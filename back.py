from flask import Flask, render_template, request
import requests

app = Flask(__name__)

def search_artists(search_term, offset=0):
    url = "https://musicbrainz.org/ws/2/artist/"
    headers = {
        "User-Agent": "TheBardApp/1.0 ( iloi05@csu.fullerton.edu )"
    }
    params = {
        "query": f'artist:"{search_term}"',
        "fmt": "json",
        "limit": 10,
        "offset": offset
    }
    response = requests.get(url, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    return data["artists"], data["count"]


@app.route("/")
def home():
    search_term = request.args.get("q", "").strip()
    offset = int(request.args.get("offset", 0))
    artists = []
    tot = 0

    if search_term:
        artists, tot = search_artists(search_term, offset)
    return render_template("home.html", artists=artists, search_term=search_term, total=tot, offset=offset)


@app.route("/favorites")
def favorites_page():
    return render_template("fav.html")

def get_artist_image(artist_name):
    url = "https://www.theaudiodb.com/api/v1/json/123/search.php"
    params = {"s": artist_name}
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    artists = data.get("artists")
    
    if not artists:
        return None

    return artists[0].get("strArtistThumb")

if __name__ == '__main__':
    app.run(debug = True)