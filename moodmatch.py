#requests library used to make HTTP requests to external APIs
import requests
from datetime import datetime

#personal API key (we are using TMDb already existing API)
API_KEY = '22ed80d327e416f838ff144080cae633'
#Base URL for TMDb API (get this and all endpoints from API Documentation)
#root of every request made (GET, PULL, PUT) add endpoints to it later
TMDB_API_URL = 'https://api.themoviedb.org/3'

#defines a function to search for movie recs based on inputted mood
#when building the actual app we make out own API to do HTTP requests into this
def get_movie_recommendations(mood = "happy", runtime = "90", max_results=5):
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
    print(genre_id)
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
        "with_runtime.lte" : user_runtime #only shows movies <= that runtime
    }

    #send the actual request to TMDb's server using GET with url and params
    response = requests.get(url, params=params)

    #response from TMDb is in JSON and this conversts it into a python dictionary so we can work with it
    data = response.json()
    # ✅ Check if results are empty and fallback
    if not data["results"] and user_runtime > 90:
        print("No results found for that mood and runtime. Trying a shorter movie...")
        params["with_runtime.lte"] = 90
        response = requests.get(url, params=params)
        data = response.json()

    # ✅ Print results (whether original or fallback)
    if not data["results"]:
        print("Still no results found. Try another mood or runtime.")
        return
    
    #here we try to get the list of results and we use '.get("results", []) so if theres an error it return 
    # an empty list instead of crashing. Then we slice the list to keep only the amount we wanted in the function def
    results = data.get("results", [])[:max_results]
    today = datetime.now().strftime("%Y-%m-%d")
    for movie in results:
        title = movie.get("title")
        overview = movie.get("overview")
        print(f"\n🎬 {title}\n{overview}")
        #creating favorites file
        user_choice = input("Would you like to save this movie to your favorites? (yes/no): ")
        if user_choice.lower() == "yes":
            with open("favorites.txt", "a") as file:
                file.write(f"{movie['title']} ({today}, Mood: {user_mood})\n")
                file.write(f"{movie['overview']}\n\n")


while True:
    favorites_choice = input("What would you like to do?\n1. Get reccomendations\n2.View favorites\n3. Exit")
    if favorites_choice == "1":
        #input essentially pastes the question into the terminal and stores the user's answer in user_mood
        user_mood = input("How are you feeling right now?").lower()
        #asking for runtime
        print("How much time do you have?")
        print("1. Less than 60 min (quick watch)")
        print("2. Up to 90 min (standard movie)")
        print("3. Up to 120 min (longer movie)")
        choice = input("Choose 1, 2, or 3: ")
        #choosing runtime based on user input
        if choice == "1":
            user_runtime = 60
        elif choice == "2":
            user_runtime = 90
        elif choice == "3":
            user_runtime = 120
        else: 
            user_runtime = 90 #default if they dont pick one
        get_movie_recommendations(user_mood, user_runtime)
    elif favorites_choice == "2":
        with open("favorites.txt", "r") as file:
            content = file.read()
            print(content)
    elif favorites_choice == "3":
         break











