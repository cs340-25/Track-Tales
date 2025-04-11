import pandas as pd
import pymongo
from flask import Flask, render_template, request
import time
import plotly.express as px
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from requests.exceptions import ReadTimeout

app = Flask(__name__)

# Setup Spotify API to access user's songs
# Spotify API setup
sp = Spotify(auth_manager=SpotifyOAuth(
    client_id="c5730c5ababe4aeba34c15b37b21d2bb",
    client_secret="c8a14935d7bb4faabd61c97b400948e2",
    redirect_uri="http://127.0.0.1:8000/callback",
    scope="user-library-read"
))

# MongoDB setup
client = pymongo.MongoClient("mongodb://127.0.0.1:27017/")
db = client["spotify_data"]
collection = db["liked_songs"]

# Function processes Json responses from API call
def fetch_liked_songs():
    print("Fetching up to 100 liked songs from Spotify...")
    songs_list = []
    limit = 50  # Max allowed per request
    offset = 0

    while len(songs_list) < 100:
        try:
            results = sp.current_user_saved_tracks(limit=limit, offset=offset)
        except ReadTimeout:
            print("ReadTimeout occurred, retrying...")
            continue

        items = results.get("items", [])
        if not items:
            break  # No more songs

        for item in items:
            track = item["track"]
            song_data = {
                "name": track["name"],
                "artist": track["artists"][0]["name"],
                "artist_id": track["artists"][0]["id"],
                "album": track["album"]["name"],
                "genre": "Unknown",
                "value": 1,
                "parent": track["artists"][0]["name"]
            }
            songs_list.append(song_data)

        offset += limit
        if len(items) < limit:
            break  # Last batch

    return songs_list[:100]  # Just to be safe



# Function maps each song to its genre using its correlated artist id
def get_artist_genres(songs_list):
    print("Fetching genres for artists in batches of 20...")

    artist_ids = list({song['artist_id'] for song in songs_list if song.get('artist_id')})
    artist_genre_map = {}

    for i in range(0, len(artist_ids), 20):
        batch = artist_ids[i:i+20]
        try:
            artist_info = sp.artists(batch)
            for artist in artist_info['artists']:
                genre = artist['genres'][0] if artist['genres'] else "Unknown"
                artist_genre_map[artist['id']] = genre
        except Exception as e:
            print(f"Error fetching batch: {e}")
            continue

    for song in songs_list:
        song['genre'] = artist_genre_map.get(song['artist_id'], "Unknown")

    return songs_list


# Fetch data from MongoDB and convert it into a DataFrame
def fetch_data():
    print("Fetching data from MongoDB...")
    plotly_data = collection.find()
    data = list(plotly_data)
    df = pd.DataFrame(data)
    df["parent"] = df["parent"].fillna("Root")
    return df

from flask import request

@app.route('/apply_filter', methods=["GET"])
def apply_filter():
    # Get the selected genres from the request (checkbox values)
    selected_genres = request.args.getlist("genres")
    print("Selected genres:", selected_genres)
    
    # Fetch data from MongoDB and filter by genres if any are selected
    df = fetch_data()

    # Filter by selected genres if there are any
    if selected_genres:
        df = df[df['genre'].isin(selected_genres)]
    
    # Create Plotly treemap or sunburst based on the view parameter
    view_type = request.args.get("view", "treemap")
    
    if view_type == "sunburst":
        fig = px.sunburst(df,
                          path=["genre", "artist", "album", "name"],
                          values="value",
                          hover_data=["name"],
                          title="Spotify Liked Songs Sunburst")
    else:  # Default to treemap
        fig = px.treemap(df,
                         path=["genre", "artist", "album", "name"],
                         values="value",
                         hover_data=["name"],
                         title="Spotify Liked Songs Treemap")

    # Update Plotly figure
    fig.update_traces(root_color="lightgrey")
    fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))

    # Convert Plotly figure to HTML
    plot_html = fig.to_html(full_html=False)

    # Fetch genres for the checkbox list
    genres = df['genre'].unique()

    return render_template('index.html', plot_html=plot_html, genres=genres, selected_genres=selected_genres)


@app.route('/', methods=["GET", "POST"])
def home():
    selected_genres = request.args.getlist("genres")
    print("Selected genres:", selected_genres)
    
    # Fetch and filter data from MongoDB
    df = fetch_data()

    # Filter by selected genres
    if selected_genres:
        df = df[df['genre'].isin(selected_genres)]
    
    # Create Plotly visualization (Treemap or Sunburst)
    view_type = request.args.get("view", "treemap")
    if view_type == "sunburst":
        fig = px.sunburst(df,
                          path=["genre", "artist", "album", "name"],
                          values="value",
                          hover_data=["name"],
                          title="Spotify Liked Songs Sunburst")
    else:
        fig = px.treemap(df,
                         path=["genre", "artist", "album", "name"],
                         values="value",
                         hover_data=["name"],
                         title="Spotify Liked Songs Treemap")

    # Update Plotly figure
    fig.update_traces(root_color="lightgrey")
    fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))

    # Convert Plotly figure to HTML
    plot_html = fig.to_html(full_html=False)

    # Fetch unique genres for checkboxes
    genres = df['genre'].unique()

    return render_template('index.html', plot_html=plot_html, genres=genres, selected_genres=selected_genres)

if __name__ == "__main__":
    liked_songs = fetch_liked_songs()  # Initial data fetch
    songs_with_genre = get_artist_genres(liked_songs)
    print("Inserting songs into MongoDB...")
    if songs_with_genre:
        collection.drop()
        collection.insert_many(songs_with_genre)
    else:
        print("No songs to insert into MongoDB.")
    app.run(debug=True, port=8000)