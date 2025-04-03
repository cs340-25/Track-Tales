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

# Function processes Json responses from API call
def fetch_liked_songs():
    results = sp.current_user_saved_tracks()
    songs_list = []

    # Go through responses & get data about each song
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
  
# Function maps each song to its genre using its correlated artist id
def get_artist_genres(songs_list):
    # Create a dictionary to avoid duplicate API calls for the same artist
    artist_genres = {}
    
    for song in songs_list:
        artist_id = song["artist_id"]
        
        # Check if we've already looked up this artist
        if artist_id in artist_genres:
            song["genre"] = artist_genres[artist_id]
        else:
            try:
                # Get artist info from Spotify API
                artist_info = sp.artist(artist_id)
                genre = "Unknown"

                # Use the first genre if available
                if "genres" in artist_info and artist_info["genres"]:
                    genre = artist_info["genres"][0]
                
                # Store genre for future reference
                artist_genres[artist_id] = genre
                song["genre"] = genre
                except Exception as e:
                    print(f"Error fetching genre for {song['artist']}: {e}")
    
    return songs_list

# Fetch data from MongoDB and convert it into a DataFrame
def fetch_data():
    plotly_data = collection.find()
    data = list(plotly_data)
    df = pd.DataFrame(data)
    df["parent"] = df["parent"].fillna("Root")
    return df


if __name__ == "__main__":
    liked_songs = fetch_liked_songs()  # Initial data fetch
    songs_with_genre = get_artist_genre(liked_songs)
    if songs_with_genres:
      collection.insert_many(songs_with_genres)
    app.run(debug=True)

