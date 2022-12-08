import praw
import sys
import re
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
from colorama import Fore, Back, Style    
from fuzzywuzzy import fuzz
from math import ceil
import pandas as pd
from IPython.display import display
from os.path import exists
import time

import reddit_secret
import spotify_secret

def parse_submission(submission):
    # parse the title
    try:
        artist_title = re.findall("([^\[]+)\[", submission.title)[0]
        split = re.split(' - | -- | — | – ', artist_title)
        # genre = re.findall("\[(.*?)\]", submission.title)[-1]
    except:
        pass
    else:
        if len(split) > 1:
            # return the artist and track
            return [submission.id, split[0].strip(), split[1].strip()]
    return [submission.id, pd.NA, pd.NA]

def get_reddit_songs(number, time, songs):
    # connect to reddit
    reddit = praw.Reddit(
        client_id=reddit_secret.client_id,
        client_secret=reddit_secret.client_secret,
        user_agent="script to get songs"
    )

    # find the songs and put them in a temporary dataframe
    new_songs = pd.DataFrame(columns=songs.columns)
    submissions = reddit.subreddit("listentothis").top(limit=number, time_filter=time)
    data = [parse_submission(submission) for submission in submissions]
    new_songs[['reddit_id', 'reddit_artist', 'reddit_track']] = data

    # add the songs to the master dataframe and remove duplicates
    songs = pd.concat([songs, new_songs], sort=False)
    songs.drop_duplicates(subset='reddit_id', inplace=True)

    return songs

def lookup_song(spotify, artist, track):
    if pd.isna(artist) or pd.isna(track):
        return pd.NA

    results = spotify.search(q='artist:' + artist + " track: " + track, type='track')
    items = results['tracks']['items']

    if len(items) > 0:
        # return the first result if we have an exact match
        return items[0]
    else:
        # do a general search
        results = spotify.search(q= track + " " + artist, type='track')
        items = results['tracks']['items']
        print(Fore.RED + f"Couldn't find song {track} by {artist}, ", end="")
        if len(items) > 0:
            # try fuzzy matching, check if artist and song name are switched
            fuzzy_ratio = max((fuzz.partial_ratio(track.lower(), items[0]['name'].lower()) + \
                fuzz.partial_ratio(artist.lower(), items[0]['artists'][0]['name'].lower()))/2, \
                (fuzz.partial_ratio(artist.lower(), items[0]['name'].lower()) + \
                fuzz.partial_ratio(track.lower(), items[0]['artists'][0]['name'].lower()))/2)
            
            if fuzzy_ratio > 85:
                print(Fore.GREEN + f"added closest match {items[0]['name']} by {items[0]['artists'][0]['name']} {fuzzy_ratio}%")
                return items[0]
            else:
                print(Fore.MAGENTA + f"closest match {items[0]['name']} by {items[0]['artists'][0]['name']} {fuzzy_ratio}%")
        else:
            print(Fore.RED + "no matches")
    
    return pd.NA

def list_has_data(x):
    if type(x) is list:
        return pd.notna(x).any()
    else:
        return pd.notna(x)

def search_spotify(spotify, songs):
    # get the songs from spotify if we don't have them yet
    spotify_songs = [lookup_song(spotify, artist, track) if pd.isna(spotify_id) else pd.NA for artist, track, spotify_id in zip(songs['reddit_artist'], songs['reddit_track'], songs['spotify_id'])]

    # add columns to the dataframe
    # if the column already has data, use that data
    # elif the song is na, set to empty string
    # else use the new song data

    songs['spotify_id'] = [id if not pd.isna(id) \
        else "" if pd.isna(song)  \
        else song['id'] for song, id in zip(spotify_songs, songs['spotify_id'])]
    songs['spotify_artist'] = [artist if not pd.isna(artist) \
        else "" if pd.isna(song)  \
        else song['artists'][0]['name'] for song, artist in zip(spotify_songs, songs['spotify_artist'])]
    songs['spotify_track'] = [track if not pd.isna(track) \
        else "" if pd.isna(song)  \
        else song['name'] for song, track in zip(spotify_songs, songs['spotify_track'])]
    songs['spotify_genre'] = [genre if list_has_data(genre) \
        else "" if pd.isna(song)  \
        else spotify.artist(song['artists'][0]['uri'])['genres'] for song, genre in zip(spotify_songs, songs['spotify_genre'])]

    # songs['spotify_id'] = [song['id'] if not pd.isna(song) else id for song, id in zip(spotify_songs, songs['spotify_id'])]
    # songs['spotify_artist'] = [song['artists'][0]['name'] if not pd.isna(song) else artist for song, artist in zip(spotify_songs, songs['spotify_artist'])]
    # songs['spotify_track'] = [song['name'] if not pd.isna(song) else track for song, track in zip(spotify_songs, songs['spotify_track'])]
    # songs['spotify_genre'] = [spotify.artist(song['artists'][0]['uri'])['genres'] if not pd.isna(song) else genres for song, genres in zip(spotify_songs, songs['spotify_genre'])]
    return songs

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
    start = time.time()
    if exists("songs.pkl"):
        # load the pickle
        songs = pd.read_pickle("songs.pkl")
    else:
        # create empty dataframe
        songs = pd.DataFrame(columns=["reddit_id", "reddit_artist", "reddit_track", "spotify_id", "spotify_artist", "spotify_track", "spotify_genre"])

    songs = get_reddit_songs(1000, "all", songs)

    # connect to spotify
    SPOTIFY_CLIENT_ID = spotify_secret.client_id
    SPOTIFY_CLIENT_SECRET = spotify_secret.client_secret
    SPOTIFY_REDIRECT_URI = "https://localhost:8888/callback"
    scope = "playlist-modify-private"
    auth_manager = SpotifyOAuth(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI, scope=scope)
    spotify = spotipy.Spotify(auth_manager=auth_manager)

    # spotify documentation: https://developer.spotify.com/documentation/web-api/reference/
    # search spotify for the tracks
    songs = search_spotify(spotify, songs)

    # update the stored songs
    songs.to_pickle("songs.pkl")

    # write to csv
    songs.to_csv("songs.csv")
    print(Fore.WHITE, end="")
    display(songs)

    end = time.time()

    print("Duration: " + str(end-start))

    # # clear playlist
    # playlist_id = 'spotify:user:spotifycharts:playlist:1npO7ZQgRHerQuAOI0rjle'
    # clear_playlist(spotify, playlist_id)
    # print(Fore.WHITE + "Cleared playlist")

    # # batch add songs
    # n = 100
    # batched_ids = [track_ids[i:i + n] for i in range(0, len(track_ids), n)]

    # for ids in batched_ids:
    #     # add the songs
    #     spotify.playlist_add_items(playlist_id, ids)

    # print(Fore.GREEN + "Finished!")

if __name__ == "__main__":
    main()
