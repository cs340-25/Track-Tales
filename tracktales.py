import pymongo
from flask import Flask, render_template
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth

# Setup Spotify API to access user's songs
sp = Spotify(auth_manager = SpotifyOAuth(client_id = "CLIENT_ID", 
                                         client_secret = "CLIENT_SECRET", 
                                         redirect_uri = "http://localhost:8888/callback", scope="user-library-read"))
results = sp.current_user_saved_tracks()

# MongoDB setup
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["spotify_data"]
collection = db["liked_songs"]

if __name__ == "__main__":
    # Clear old data and insert new data
    collection.delete_many({})
    collection.insert_many(songs_list)

    app.run(debug=True)

# Function processes Json responses from API call
def fetch_liked_songs():
    results = sp.current_user_saved_tracks()
    songs_list = []

    # Go through responses & get various data from each song
    for item in results["items"]:
        track = item["track"]
        song_data = {
            "name": track["name"],
            "artist": track["artists"][0]["name"],
            "artist_id": track["artists"][0]["id"],  # Needed for genre lookup
            "album": track["album"]["name"],
            "genre": "Unknown",
            "value": 1,
            "parent": track["artists"][0]["name"]
        }
        # Add the song's data to a song list array
        songs_list.append(song_data)

    return songs_list
  
  try:
    artist_info = sp.artist(artist_id)
    if "genres" in artist_info and artist_info["genres"]:
        genre = artist_info["genres"][0]  # Use the first genre if available
except Exception as e:
  print(f"Error fetching genre for {song['artist']}: {e}")
