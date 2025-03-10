# Setup Spotify API to access user's songs
sp = Spotify(auth_manager = SpotifyOAuth(client_id = "CLIENT_ID", 
                                         client_secret = "CLIENT_SECRET", 
                                         redirect_uri = "http://localhost:8888/callback", scope="user-library-read"))
results = sp.current_user_saved_tracks()

# MongoDB setup
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["spotify_data"]
collection = db["liked_songs"]
