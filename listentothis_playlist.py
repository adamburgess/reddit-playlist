import praw
import sys
import re
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
from colorama import Fore, Back, Style    
from fuzzywuzzy import fuzz
from math import ceil

import reddit_secret
import spotify_secret

def get_reddit_songs(number, time):
    # connect to reddit
    reddit = praw.Reddit(
        client_id=reddit_secret.client_id,
        client_secret=reddit_secret.client_secret,
        user_agent="script to get songs"
    )

    # find the top songs
    artists = []
    tracks = []
    for submission in reddit.subreddit("listentothis").top(limit=number, time_filter=time):
        try:
            artist_title = re.findall("([^\[]+)\[", submission.title)[0]
            split = re.split(' - | -- | — | – ', artist_title)
            genre = re.findall("\[(.*?)\]", submission.title)[-1]
        except:
            print(Fore.YELLOW + "Title wrong format: ", submission.title)
        else:
            if len(split) > 1:
                
                artists.append(split[0].strip())
                tracks.append(split[1].strip())

    return artists[0:number], tracks[0:number]

def search_spotify(spotify, artists, tracks):
    track_ids = []
    for i, name in enumerate(artists):
        track = tracks[i]
        results = spotify.search(q='artist:' + name + " track: " + track, type='track')
        items = results['tracks']['items']

        if len(items) > 0:
            track_ids.append(items[0]['id'])
        else:
            # do a general search
            results = spotify.search(q= track + " " + name, type='track')
            items = results['tracks']['items']
            print(Fore.RED + f"Couldn't find song {track} by {name}, ", end="")
            if len(items) > 0:
                # try fuzzy matching, check if artist and song name are switched
                fuzzy_ratio = max((fuzz.partial_ratio(track.lower(), items[0]['name'].lower()) + \
                    fuzz.partial_ratio(name.lower(), items[0]['artists'][0]['name'].lower()))/2, \
                    (fuzz.partial_ratio(name.lower(), items[0]['name'].lower()) + \
                    fuzz.partial_ratio(track.lower(), items[0]['artists'][0]['name'].lower()))/2)
                
                if fuzzy_ratio > 85:
                    print(Fore.GREEN + f"added closest match {items[0]['name']} by {items[0]['artists'][0]['name']} {fuzzy_ratio}%")
                    track_ids.append(items[0]['id'])
                else:
                    print(Fore.MAGENTA + f"closest match {items[0]['name']} by {items[0]['artists'][0]['name']} {fuzzy_ratio}%")
            else:
                print(Fore.RED + "no matches")

    return track_ids

def clear_playlist(spotify, playlist_id):
    # go over each page of the playlist
    while True:
        # get tracks in the playlist
        results = spotify.playlist(playlist_id)
        track_ids = [item['track']['id'] for item in results['tracks']['items']]
        if len(track_ids) == 0:
            break

        # clear playlist
        results = spotify.playlist_remove_all_occurrences_of_items(
            playlist_id, track_ids)

def main():
    artists, tracks = get_reddit_songs(300, "all")

    # connect to spotify
    SPOTIFY_CLIENT_ID = spotify_secret.client_id
    SPOTIFY_CLIENT_SECRET = spotify_secret.client_secret
    SPOTIFY_REDIRECT_URI = "https://localhost:8888/callback"
    scope = "playlist-modify-private"
    auth_manager = SpotifyOAuth(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI, scope=scope)
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    # spotify documentation: https://developer.spotify.com/documentation/web-api/reference/
    # search spotify for the tracks
    track_ids = search_spotify(spotify, artists, tracks)

    # remove duplicates
    track_ids = [*set(track_ids)]

    # clear playlist
    playlist_id = 'spotify:user:spotifycharts:playlist:1npO7ZQgRHerQuAOI0rjle'
    clear_playlist(spotify, playlist_id)
    print(Fore.WHITE + "Cleared playlist")

    # batch add songs
    n = 100
    batched_ids = [track_ids[i:i + n] for i in range(0, len(track_ids), n)]

    for ids in batched_ids:
        # add the songs
        spotify.playlist_add_items(playlist_id, ids)

    print(Fore.GREEN + "Finished!")

main()

#spotify.playlist_add_items(playlist_id, [id])

