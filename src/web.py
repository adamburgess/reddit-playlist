from flask import Flask
from listentothis_playlist import get_reddit_songs
import pandas as pd

app = Flask(__name__)

@app.route("/")
def hello_world():
    songs = pd.DataFrame(columns=["reddit_id", "reddit_artist", "reddit_track", "spotify_id", "spotify_artist", "spotify_track", "spotify_genre"])
    songs = get_reddit_songs(800, "all", songs)
    return songs.to_html()
