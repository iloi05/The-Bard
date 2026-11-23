from flask import Flask, render_template, request, redirect, url_for, jsonify
from concurrent.futures import ThreadPoolExecutor
import requests
import re
import threading
import time
import requests

app = Flask(__name__)

HEADERS = {
    "User-Agent": "TheBardApp/1.0 ( iloi05@csu.fullerton.edu)"
}
PG_SIZE = 24
GENRES = ["rock", "pop", "jazz", "hip hop", "country", "electronic", "classical", "r&b", "metal", "folk"]
TYPES = {"person": "Solo artist", "group": "Band / group", "orchestra": "Orchestra", "choir": "Choir"}
ROLES = {"composer": "Composer", "singer-songwriter": "Singer-songwriter", "rapper": "Rapper", "dj": "DJ"}
MUSICIAN_TYPES = "(type:person OR type:group OR type:orchestra OR type:choir)"
DEFAULT_GENRES = '(tag:rock OR tag:pop OR tag:jazz OR tag:"hip hop" OR tag:country OR tag:electronic)'

def lucene_escape(text):
    return text.replace("\\", "\\\\").replace('"', '\\"')

def build_query(search_term, genre, artist_type, role):
    parts = []
    if search_term:
        parts.append(f'artist:"{lucene_escape(search_term)}"')

    if artist_type in TYPES:
        parts.append(f"type:{artist_type}")
    else:
        parts.append(MUSICIAN_TYPES)

    if genre in GENRES:
        parts.append(f'tag:"{genre}"')
    if role in ROLES:
        parts.append(f'tag:"{role}"')

    if not (search_term or genre or role):
        parts.append(DEFAULT_GENRES)
    return " AND ".join(parts)

_mb_lock = threading.Lock()
_mb_last_call = 0.0

def _rate_limit_musicbrainz():
    global _mb_last_call
    with _mb_lock:
        wait = 1.0 - (time.monotonic() - _mb_last_call)
        if wait > 0:
            time.sleep(wait)
        _mb_last_call = time.monotonic()

def search_artists(query, offset=0):
    _rate_limit_musicbrainz()
    response = requests.get(
        "https://musicbrainz.org/ws/2/artist/",
        headers=HEADERS,
        params={"query": query, "fmt": "json",
                "limit": PG_SIZE, "offset": offset},
                timeout=10,
    )
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
    return render_template("home.html")

@app.route("/explore")
def explore_page():
    search_term = request.args.get("q", "").strip()
    genre = request.args.get("genre", "")
    artist_type = request.args.get("type", "")
    role = request.args.get("role", "")
    sort = request.args.get("sort", "")
    offset = max(request.args.get("offset", 0, type=int), 0)

    query = build_query(search_term, genre, artist_type, role)
    try:
        artists, tot = search_artists(query, offset)
    except requests.RequestException as e:
        print("MusicBrainz error:", e)
        artists, tot = [], 0
    with ThreadPoolExecutor(max_workers=3) as pool:
        images = list(pool.map(get_artist_image, [a["name"] for a in artists]))
    for artist, image in zip(artists, images):
        artist["image"] = image

    if sort in ("az", "za"):
        artists.sort(key=lambda a: a["name"].lower(), reverse=(sort == "za"))

    filters = dict(q=search_term, genre=genre, type=artist_type, role=role, sort=sort)

    return render_template("explore.html", artists=artists, search_term=search_term, total=tot, offset=offset, pg_size=PG_SIZE, filters=filters, genres=GENRES, types=TYPES, roles=ROLES)

_suggest_cache = {}

@app.route("/api/search")
def search():
    term = request.args.get("q", "").strip()
    if len(term) < 2:
        return jsonify([])
    key = term.lower()
    if key in _suggest_cache:
        return jsonify(_suggest_cache[key])

    parts = [f'artist:"{lucene_escape(term)}"^2']
    last_word = re.sub(r"\W", "", term.split()[-1])
    if last_word:
        parts.append(f"artist:{last_word.lower()}*")
    query = f"({' OR '.join(parts)}) AND {MUSICIAN_TYPES}"

    try:
        artists, _ = search_artists(query)
    except requests.RequestException as e:
        print("MusicBrainz unavailable:", e)
        return jsonify({"error": "MuscBrainz unavailable"}), 503

    results = [{
        "id": a["id"],
        "name": a["name"],
        "disambiguation": a.get("disambiguation", ""),
        "country": a.get("country", ""),
    } for a in artists[:8]]
    _suggest_cache[key] = results
    return jsonify(results)

@app.route("/favorites")
def favorites_page():
    return render_template("fav.html")

if __name__ == '__main__':
    app.run(debug = True)