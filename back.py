from flask import Flask, render_template, request
from concurrent.futures import ThreadPoolExecutor
import requests

app = Flask(__name__)

HEADERS = {
    "User-Agent": "TheBardApp/1.0 ( iloi05@csu.fullerton.edu)"
}

MUSICIAN_TYPES = "(type:person OR type:group OR type:orchestra OR type:choir)"
DEFAULT_QUERY = f'{MUSICIAN_TYPES} AND (tag:rock OR tag:pop OR tag:jazz OR tag:"hip hop" OR tag:country OR tag:electronic)'

def search_artists(search_term, offset=0):
    url = "https://musicbrainz.org/ws/2/artist/"
    if search_term:
        query = f'artist:"{search_term}" AND {MUSICIAN_TYPES}'
    else:
        query = DEFAULT_QUERY

    params = {
        "query": query,
        "fmt": "json",
        "limit": 25,
        "offset": offset
    }
    response = requests.get(url, headers=HEADERS, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    return data["artists"], data["count"]

_image_cache = {}

def get_artist_image(artist_name):
    if artist_name in _image_cache:
        return _image_cache[artist_name]
    try:
        response = requests.get(
            "https://www.theaudiodb.com/api/v1/json/123/search.php",
            params = {"s": artist_name},
            timeout=5,
        )
        response.raise_for_status()
        artists = response.json().get("artists")
    except (requests.RequestException, ValueError):
        return None
    
    image = artists[0].get("strArtistThumb") if artists else None
    _image_cache[artist_name] = image
    return image

@app.route("/")
def home():
    search_term = request.args.get("q", "").strip()
    offset = int(request.args.get("offset", 0))
    try:
        artists, tot = search_artists(search_term, offset)
    except requests.RequestException as e:
        print("MusicBrainz error:", e)
        artists, tot = [], 0
    print("from MusicBrainz:", len(artists))
    with ThreadPoolExecutor(max_workers=3) as pool:
        images = list(pool.map(get_artist_image, [a["name"] for a in artists]))
    for artist, image in zip(artists, images):
        artist["image"] = image

    print("after image filter:", len(artists))
    return render_template("home.html", artists=artists, search_term=search_term, total=tot, offset=offset)

@app.route("/favorites")
def favorites_page():
    return render_template("fav.html")

if __name__ == '__main__':
    app.run(debug = True)