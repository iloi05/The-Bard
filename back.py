from flask import Flask, render_template, request, redirect, url_for, jsonify
from concurrent.futures import ThreadPoolExecutor
import requests
import re
import threading
import time

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

# excapes backslashes and double quotes so user input can't break out of quoted Lucene search string
def lucene_escape(text):
    return text.replace("\\", "\\\\").replace('"', '\\"')

# builds MusicBrainz Lucene query by joining clauses with AND
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

# enforces MusicBrainz's limit of one request/sec
# lock + timestamp makes any thread wait until second has passed since last call
def _rate_limit_musicbrainz():
    global _mb_last_call # reassigns _mb_last_call
    with _mb_lock:
        wait = 1.0 - (time.monotonic() - _mb_last_call)
        if wait > 0:
            time.sleep(wait)
        _mb_last_call = time.monotonic()

# calls MusicBrainz artist search, applies rate limit first
# raises HTTP erros and returns (artists, total_count)
def search_artists(query, offset=0, limit=PG_SIZE):
    _rate_limit_musicbrainz()
    response = requests.get(
        "https://musicbrainz.org/ws/2/artist/",
        headers=HEADERS,
        params={"query": query, "fmt": "json",
                "limit": limit, "offset": offset},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    return data["artists"], data["count"]

_image_cache = {}

# looks up thumbnail on TheAudioDB (uses free test key 123)
# caches image in _image_cache
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
        # fail = return none without caching so retried later
        return None
    # not-found results cached as none
    image = artists[0].get("strArtistThumb") if artists else None
    _image_cache[artist_name] = image
    return image

# render home page
@app.route("/")
def home():
    return render_template("home.html")

SORT_BATCH = 100

# this is main route
@app.route("/explore")
def explore_page():
    # reads search term, filters, sort and offset from query string (clamped to >= 0)
    search_term = request.args.get("q", "").strip()
    genre = request.args.get("genre", "")
    artist_type = request.args.get("type", "")
    role = request.args.get("role", "")
    sort = request.args.get("sort", "")
    offset = max(request.args.get("offset", 0, type=int), 0)

    query = build_query(search_term, genre, artist_type, role)
    error = False
    has_next = False
    try:
        if sort in ("az", "za"):
            # fetch 1st 100 resutls, sorts in Python & slices out current page
            batch, _ = search_artists(query, 0, limit=SORT_BATCH)
            batch.sort(key=lambda a: a["name"].lower(), reverse=(sort == "za"))
            tot = len(batch)
            artists = batch[offset:offset + PG_SIZE]
            has_next = offset + PG_SIZE < len(batch)
        else:
            # fetch PG_SIZE + 1 results & extra one tells whether next page exists without second query
            fetched, tot = search_artists(query, offset, limit=PG_SIZE + 1)
            has_next = len(fetched) > PG_SIZE
            artists = fetched[:PG_SIZE]
    except requests.RequestException as e:
        # network error shows empty list with error=True
        print("MusicBrainz error:", e)
        artists, tot = [], 0
        error = True
    # offset past end, redirect to last valid page
    if not artists and offset > 0 and tot > 0:
        last_offset = ((tot - 1) // PG_SIZE) * PG_SIZE
        # fretch images for page's artists, 3 at a time & attaches them
        return redirect(url_for("explore_page", offset=last_offset, q=search_term, genre=genre, type=artist_type, role=role, sort=sort))

    with ThreadPoolExecutor(max_workers=3) as pool:
        images = list(pool.map(get_artist_image, [a["name"] for a in artists]))
    for artist, image in zip(artists, images):
        artist["image"] = image
    # build filters
    filters = dict(q=search_term, genre=genre, type=artist_type, role=role, sort=sort)
    # render template
    return render_template("explore.html", artists=artists, search_term=search_term, offset=offset, pg_size=PG_SIZE, filters=filters, genres=GENRES, types=TYPES, roles=ROLES, has_next=has_next, error=error)

_suggest_cache = {}
# dropdown autocomplete endpoint
@app.route("/api/search")
def search():
    term = request.args.get("q", "").strip()
    if len(term) < 2:
        return jsonify([]) # for terms under 2 characters and searches repeat searches from _suggest_cache
    key = term.lower()
    if key in _suggest_cache:
        return jsonify(_suggest_cache[key])
    # builts query matching exact phrase or prefix match on last word, restricted to musician types
    parts = [f'artist:"{lucene_escape(term)}"^2']
    last_word = re.sub(r"\W", "", term.split()[-1])
    if last_word:
        parts.append(f"artist:{last_word.lower()}*")
    query = f"({' OR '.join(parts)}) AND {MUSICIAN_TYPES}"

    try:
        artists, _ = search_artists(query)
    except requests.RequestException as e:
        print("MusicBrainz unavailable:", e)
        return jsonify({"error": "MuscBrainz unavailable"}), 503 # triggers "search is busy"

    results = [{
        "id": a["id"],
        "name": a["name"],
        "disambiguation": a.get("disambiguation", ""),
        "country": a.get("country", ""),
    } for a in artists[:8]] # return first 8 results
    _suggest_cache[key] = results
    return jsonify(results)

@app.route("/favorites")
def favorites_page():
    return render_template("fav.html")

if __name__ == '__main__':
    app.run(debug = True)