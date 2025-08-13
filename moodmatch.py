#requests library used to make HTTP requests to external APIs
import requests
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import os, json, random

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
CORS(app)


#personal API key (we are using TMDb already existing API)
API_KEY = '22ed80d327e416f838ff144080cae633'
#Base URL for TMDb API (get this and all endpoints from API Documentation)
#root of every request made (GET, PULL, PUT) add endpoints to it later
TMDB_API_URL = 'https://api.themoviedb.org/3'

#defines a function to search where each movie can be watched
def get_watch_providers(movie_id):
    """Get streaming providers for a movie"""
    try:
        url = f"{TMDB_API_URL}/movie/{movie_id}/watch/providers"
        params = {"api_key": API_KEY}
        response = requests.get(url, params=params)
        
        # Add error handling for API response
        if response.status_code != 200:
            
            return {"flatrate": [], "rent": [], "buy": []}
            
        data = response.json()
        us_providers = data.get("results", {}).get("US", {})
        
        
        
        return {
            "flatrate": us_providers.get("flatrate", []),
            "rent": us_providers.get("rent", []),
            "buy": us_providers.get("buy", [])
        }
    except Exception as e:
        return {"flatrate": [], "rent": [], "buy": []}

#defines a function to search for movie recs based on inputted mood
#when building the actual app we make out own API to do HTTP requests into this
def get_movie_recommendations(mood="happy", runtime=90, max_results=5):
    """Get movie recommendations based on mood and runtime"""
    try:
        mood_to_genres = {
            "happy": [12, 35, 16, 10751],      # Adventure, Comedy, Animation, Family
            "sad": [18, 10749],        # Drama, Romance
            "stressed": [16, 35, 10751],   # Animation, Comedy, Family
            "dramatic": [18, 36, 10752],   # Drama, History, War
            "lonely": [10749, 35, 18],     # Romance, Comedy, Drama
            "curious": [878, 99, 53],      # Sci-Fi, Documentary, Thriller
            "kid-friendly": [16, 10751, 14], # Animation, Family, Fantasy
            "angry": [28, 80, 53],         # Action, Crime, Thriller
            "excited": [12, 28, 14],       # Adventure, Action, Fantasy
            "romantic": [10749, 35, 18],   # Romance, Comedy, Drama
            "scary": [27, 53, 9648],       # Horror, Thriller, Mystery
            "funny": [35, 10751, 16],      # Comedy, Family, Animation
        }
        
        genre_list = mood_to_genres.get(mood.lower(), [12, 35])
        selected_genres = random.sample(genre_list, min(2, len(genre_list)))
        genre_ids = ",".join(map(str, selected_genres))
        # Random page number (1-5) to get different results each time
        random_page = random.randint(1, 5)
        # Vary sorting method randomly
        sort_options = [
            "popularity.desc",
            "vote_average.desc", 
            "release_date.desc",
            "vote_count.desc"
        ]
        sort_by = random.choice(sort_options)
        
        url = f"{TMDB_API_URL}/discover/movie"
        
        params = {
            "api_key": API_KEY,
            "with_genres": genre_ids,
            "language": "en-US",
            "sort_by": "popularity.desc",
            "vote_average.gte": 7.0,
            "include_adult": False,
            "with_runtime.lte": runtime,
            "page": random_page
        }

        # Add some randomness with additional filters
        if random.choice([True, False]):
            # Sometimes filter by release date to get newer or older movies
            if random.choice([True, False]):
                params["primary_release_date.gte"] = "2015-01-01"  # Newer movies
            else:
                params["primary_release_date.gte"] = "2000-01-01"  # Older movies
        

        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            return []
            
        data = response.json()
        
        # Fallback if no results
        if not data.get("results") and int(runtime) > 90:
            params["with_runtime.lte"] = 90
            params["page"] = 1
            response = requests.get(url, params=params)
            data = response.json()

        if not data.get("results"):
            return []
        
        results = data.get("results", [])
        
        # Filter out movies we might have seen before by checking if they're too popular
        # This helps avoid the same blockbusters appearing every time
        if len(results) > max_results * 2:
            # Skip the most popular ones sometimes
            start_index = random.randint(0, min(10, len(results) - max_results))
            results = results[start_index:]
        
        # Randomly shuffle the results and take max_results
        random.shuffle(results)
        results = results[:max_results]
        
        # Build the response with watch providers
        recommendations = []
        
        for i, movie in enumerate(results):
            if movie.get("title") and movie.get("overview"):
                movie_id = movie.get("id")
                
                watch_providers = get_watch_providers(movie_id) if movie_id else {"flatrate": [], "rent": [], "buy": []}
                
                movie_data = {
                    "id": movie_id,
                    "title": movie.get("title"),
                    "overview": movie.get("overview"),
                    "poster_path": movie.get("poster_path"),
                    "release_date": movie.get("release_date"),
                    "vote_average": movie.get("vote_average"),
                    "watch_providers": watch_providers
                }
                
                recommendations.append(movie_data)
        
        
        return recommendations
        
    except Exception as e:
        return []
    
# Handle preflight OPTIONS requests
@app.route('/recommend', methods=['OPTIONS'])
@app.route('/save_favorite', methods=['OPTIONS']) 
@app.route('/favorites', methods=['OPTIONS'])
@app.route('/clear_favorites', methods=['OPTIONS'])
def handle_options():
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response


@app.route("/save_favorite", methods=["POST"])
def save_favorite():
    data = request.get_json() or {}
    movie_id = data.get("id")
    title = data.get("title")
    overview = data.get("overview")
    mood = data.get("mood")
    poster_path = data.get("poster_path")
    watch_providers = data.get("watch_providers", {"flatrate": [], "rent": [], "buy": []})
    release_date = data.get("release_date")
    vote_average = data.get("vote_average")

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
        "watch_providers": watch_providers,
        "release_date": release_date,
        "vote_average": vote_average,
    })
    _save_favorites(items)
    return {"message": "Favorite saved successfully!"}, 200


@app.route("/recommend", methods=["POST"])
def get_movie_recommendations_api():
    data = request.get_json()
    mood = data.get("mood", "").lower()
    runtime = data.get("runtime", 90)
    
    recommendations = get_movie_recommendations(mood, runtime)
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
    app.run(host='0.0.0.0', port=5001, debug=True)















