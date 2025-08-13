#requests library used to make HTTP requests to external APIs
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import os, json

FAVORITES_FILE = "favorites.json"

def _load_favorites():
    if not os.path.exists(FAVORITES_FILE):
        return []
    try:
        with open(FAVORITES_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def _save_favorites(items):
    with open(FAVORITES_FILE, "w") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)

#personal API key (we are using TMDb already existing API)
API_KEY = '22ed80d327e416f838ff144080cae633'
#Base URL for TMDb API (get this and all endpoints from API Documentation)
#root of every request made (GET, PULL, PUT) add endpoints to it later
TMDB_API_URL = 'https://api.themoviedb.org/3'

#defines a function to search where each movie can be watched
def get_watch_providers(movie_id):
    """Get streaming providers for a movie"""
    url = f"{TMDB_API_URL}/movie/{movie_id}/watch/providers"
    params = {"api_key": API_KEY}
    response = requests.get(url, params=params)
    data = response.json()
    us_providers=data.get("results", {}).get("US", {})
    return{
        "flatrate": us_providers.get("flatrate", []),
        "rent": us_providers.get("rent", []),
        "buy": us_providers.get("buy", [])
    }

#defines a function to search for movie recs based on inputted mood
#when building the actual app we make out own API to do HTTP requests into this
def get_movie_recommendations(mood = "happy", runtime = 90, max_results=5):
    #here we are mapping certain moods someone might imput to genre ids in the API
    mood_to_genre_id = {"happy" : 12,
                        "sad" : 35,
                        "stressed" : 16,
                        "dramatic": 18,
                        "lonely": 10749,
                        "curious": 878,
                        "kid-friendly": 10751,
                        "angry": 28}
    #getting the genre_id based on mood (using lower to make it case_sensitive)
    genre_id = mood_to_genre_id.get(mood.lower(), 12)
    #by adding endpoint'/search/movie' we are sending a GET request to API to search for movies
    url = f"{TMDB_API_URL}/discover/movie"
    # dictionary that holds query parameters sent with every request:
    #'api-key' = personal API key, 'with_genres' = id that represents each genre of movie
    #'language' = sets the language of the results, 'include_adult' = False means not including adult content
    #'sort_by" = sorts by popularity, 'vote_average.get' = gives only movies of higher than a 6 rating
    #also found in API directory
    params = {
        "api_key": API_KEY,
        "with_genres": genre_id,
        "language": "en-US",
        "sort_by": "popularity.desc",
        "vote_average.gte" : 6,
        "include_adult": False,
        "with_runtime.lte" : runtime #only shows movies <= that runtime
    }

    #send the actual request to TMDb's server using GET with url and params
    response = requests.get(url, params=params)

    #response from TMDb is in JSON and this conversts it into a python dictionary so we can work with it
    data = response.json()
    # ✅ Check if results are empty and fallback
    if not data.get("results") and int(runtime) > 90:
        print("No results found for that mood and runtime. Trying a shorter movie...")
        params["with_runtime.lte"] = 90
        response = requests.get(url, params=params)
        data = response.json()

    # ✅ Print results (whether original or fallback)
    if not data["results"]:
        print("Still no results found. Try another mood or runtime.")
        return
    
    #defined results as an array of max_results length
    results = data.get("results", [])[:max_results]
    #Returns cleaned-up list for user
    return [
    {
        "id": movie.get("id"),
        "title": movie.get("title"),
        "overview": movie.get("overview"),
        "poster_path": movie.get("poster_path"),
        "watch_providers": get_watch_providers(movie.get("id"))
    }
    for movie in results if movie.get("title") and movie.get("overview")
    ]

@app.route("/save_favorite", methods=["POST"])
def save_favorite():
    data = request.get_json() or {}
    movie_id = data.get("id")
    title = data.get("title")
    overview = data.get("overview")
    mood = data.get("mood")
    poster_path = data.get("poster_path")

    if not title or not overview:
        return {"message": "Missing title or overview."}, 400

    items = _load_favorites()

    #Duplicate Check
    if movie_id is not None:
        if any(str(it.get("id")) == str(movie_id) for it in items) :
            return {"message": "Already in favorites."}, 409
        
    else:
        if any(
            (it.get("title") or "").strip().lower() == title.strip().lower()
            for it in items
        ):
            return {"message": "Already in favorites"}, 409
        

    items.append({
        "title": title,
        "overview": overview,
        "mood": mood,
        "id": movie_id,
        "poster_path": poster_path,
        "date": datetime.now().strftime("%Y-%m-%d"),
    })
    _save_favorites(items)
    return {"message": "Favorite saved successfully!"}, 200


@app.route("/recommend", methods=["POST"])
def get_movie_recommendations_api():
    data = request.get_json()
    mood = data.get("mood", "").lower()
    runtime = data.get("runtime", 90)
    
    recommendations = get_movie_recommendations(mood, runtime)
    print("Sending these recommendations:", recommendations)
    return jsonify({"movies": recommendations})

#creates favorites file (seperate tab)
@app.route("/favorites", methods=["GET"])
def get_favorites():
    return jsonify(_load_favorites()), 200
    
#opens favorite file in write mode and clears content
@app.route("/clear_favorites", methods=["POST"])
def clear_favorites():
    _save_favorites([])
    return jsonify({"message": "Favorites cleared!"}), 200

    
#default error handling
@app.errorhandler(Exception)
def handle_error(e):
    print(f"Unhandled Exception: {e}")
    return jsonify({"error": str(e)}), 500



def cli_mode():
    while True:
        favorites_choice = input("What would you like to do?\n1. Get recommendations\n2. View favorites\n3. Exit\n")
        
        if favorites_choice == "1":
            user_mood = input("How are you feeling right now? ").lower()
            print("How much time do you have?")
            print("1. Less than 60 min (quick watch)")
            print("2. Up to 90 min (standard movie)")
            print("3. Up to 120 min (longer movie)")
            choice = input("Choose 1, 2, or 3: ")

            if choice == "1":
                user_runtime = 60
            elif choice == "2":
                user_runtime = 90
            elif choice == "3":
                user_runtime = 120
            else:
                user_runtime = 90  # default

            get_movie_recommendations(user_mood, user_runtime)

        elif favorites_choice == "2":
            with open("favorites.txt", "r") as file:
                content = file.read()
                print(content)
        elif favorites_choice == "3":
            break
        else:
            print("Invalid option. Try again.")

if __name__ == "__main__":
    app.run(debug=True)















