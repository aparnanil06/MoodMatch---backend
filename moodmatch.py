#requests library used to make HTTP requests to external APIs
import requests
import sqlite3
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import os, json, random
from functools import wraps
import firebase_admin
from firebase_admin import credentials, auth

# Initialize Firebase Admin SDK
# Download your service account key from Firebase Console → Project Settings → Service Accounts
# Place it in your project directory and update the path below
try:
    # For production - use environment variables
    if os.getenv('FIREBASE_PRIVATE_KEY'):
        firebase_config = {
            "type": "service_account",
            "project_id": os.getenv('moodmatch-bb2c6'),
            "private_key_id": os.getenv('cda7219556aeb9aa18923fe2442912416e34159a'),
            "private_key": os.getenv('-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCsOHymqxw+4IDk\nIiEeOhSvnDKkkn6w9BByC90R0S8VyQ9s6aWqMJKU94tZCfgT1tEM169CkkgtzSkL\nHJzJa3dLLly9yIf2IRbd165H9dHXRr//UJ7MfOWK4DiW1SXsZ7I/fXHlOEMp4zTs\nxFVDOQQkcboo7XRIxy4kIc9aj1L0/TrzTrNMCqDPF05JxVvfkpGc5wkKfhOpE9EE\nEJYuARK3vwvmkr+AU0ozvchV034ARbzGSYc1rAnRmJUlrTGDYJs66RskMLlhhIuv\nb6VwLW/kVeB0sy3QTlfGq2iDPyOZ40SBgOyyo0Ynav6haZSzgsnp8Eu1UjI6MTyS\n0O0Sbwa3AgMBAAECggEACyGrjOpKbRX9vsEl+touNBuYemKtpapg1b5Gj7xBmtrg\nEF4ZwyJYlyBY9WxbiIy9/mKChX8HA07bdEhpKeu0Tju06t9nSlVhMP2b2jLdWVjN\nWCdR3E3GWG+duMIWLW2Wa9wj3HkCfladOSCHkkzBI8nmCncuqPWW2ecFjAjvh74r\nR8rM+IytLwcsmQehbJrtUjC1Lo36+g5FTSxnmAHgeET5lbq6N2TDLwY8D+IxM5P1\nh0cjv1NruuhUUEfoDxfNjkrCJs/cdeNGHBWjo+m3TqufiwUEm15Uz/NY0SOUEifo\nOnlGvZ49MjEzx0R2mcZn+su60krn3a9ZUIROUbs9AQKBgQDU+2/A+imxgNsqz5pG\n7zZgNmbJdzimHjkYrQuiXofzRRYqXxFatL31nDo8tIG/tJoGp+NTWz/c/kKF3v21\n3KYR3q3h2yAfdjrAaOB73E/mXfQY7REYi5u9iEzWQvoZ1LV1tIP8vSCcBc/+4kIn\nFfWV0rBpw7cBdBwdy8QwBAuTVwKBgQDPAWokKDNDNNSyks/MZ0YUFSeRkaEyEqKt\nAwiINl1LUHzFzsyTzk3cs/QCMfvcZ+JG9zKHlk2ID8RWyyTyZ6S9sNIKiQDuqcsf\nrkef72bkJzO3LHbVqwRMggvZxqbeZPf/fOHKErORNMythw5qlE4BAvYODzxMibIR\nfXawmr5roQKBgATjQE1NcGeCbYUt/nxiQP00QmedNM+bIfRPBFVVlgkfLMMMK3nJ\nbBKW4z9BZTjhDCfa8nyXO3/21c/8rhXeWnFOiu8D+FjAfdisj3pINA01WsS3rAzE\nJ27SEfFY2CR/nSp2WhESxgzOlVdkGeCLwHcPvryuoSSHZZ3Jb1cqwJlBAoGAeI+R\nWteS64xkaFB698gaF24uqmhPopMZ7Xu7x2EqOsf4s1f67AaWcHjaH0EvN7HFJqGn\n6zHNm/Xa2tXbgdZ9KwFFg19BjL6VD7F4A5zxpuVyCDe8Sjsc+NYwwrggzZuumD0K\nX58+t84xessSyV3whEROO+gBrW3wqKEStE6boqECgYBZ5x75y7PnZ1ppikWIlPKe\nZBInyXILMgPQPq107hEP+cKWelaVXPw3uzBKpyGArHQfY0WMv7+1uWdI/hRNDpOc\nuI60/RLpvjHZVne+SySR+95qUdcevlCvZoNqf6cxeTKpwBYLTJ3ksgWtwGsSFB3v\nhoGHShICyNPh8HQZYMmH+g==\n-----END PRIVATE KEY-----\n').replace('\\n', '\n'),
            "client_email": os.getenv('firebase-adminsdk-fbsvc@moodmatch-bb2c6.iam.gserviceaccount.com'),
            "client_id": os.getenv('100511670367498861376'),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
        cred = credentials.Certificate(firebase_config)
        print("Using Firebase environment variables")
    else:
        # For local development
        cred = credentials.Certificate("moodmatch-bb2c6-firebase-adminsdk-fbsvc-cda7219556.json")
        print("Using Firebase JSON file for local development")
    
    firebase_admin.initialize_app(cred)
    print("Firebase Admin initialized successfully")
except Exception as e:
    print(f"Firebase Admin initialization failed: {e}")

# Initialize SQLite database for user-specific favorites
def init_db():
    conn = sqlite3.connect('user_favorites.db')
    cursor = conn.cursor()
    
    # Create user_favorites table with Firebase UID
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firebase_uid TEXT NOT NULL,
            movie_id INTEGER,
            title TEXT NOT NULL,
            overview TEXT NOT NULL,
            mood TEXT,
            poster_path TEXT,
            watch_providers TEXT,
            release_date TEXT,
            vote_average REAL,
            date_saved TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(firebase_uid, movie_id)
        )
    ''')
    
    # Create users table to store user profile information
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            firebase_uid TEXT PRIMARY KEY,
            email TEXT,
            display_name TEXT,
            photo_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database when app starts
init_db()

app = Flask(__name__)
CORS(app)

# Firebase authentication decorator
def firebase_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get the Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid authorization header"}), 401
        
        # Extract the token
        id_token = auth_header.split('Bearer ')[1]
        
        try:
            # Verify the Firebase ID token
            decoded_token = auth.verify_id_token(id_token)
            # Add the user info to the request context
            request.firebase_user = decoded_token
            return f(*args, **kwargs)
        except Exception as e:
            print(f"Firebase token verification failed: {e}")
            return jsonify({"error": "Invalid authentication token"}), 401
    
    return decorated_function

# Optional decorator for endpoints that can work with or without auth
def firebase_auth_optional(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get the Authorization header
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            # Extract the token
            id_token = auth_header.split('Bearer ')[1]
            
            try:
                # Verify the Firebase ID token
                decoded_token = auth.verify_id_token(id_token)
                # Add the user info to the request context
                request.firebase_user = decoded_token
            except Exception as e:
                print(f"Firebase token verification failed: {e}")
                request.firebase_user = None
        else:
            request.firebase_user = None
            
        return f(*args, **kwargs)
    
    return decorated_function

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
            "sort_by": sort_by,
            "vote_average.gte": 7.0,
            "vote_count.gte": 100,
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
        
        for movie in results:
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

# Store or update user information after login
def store_user_info(firebase_user):
    """Store user information in database after successful login"""
    conn = sqlite3.connect('user_favorites.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO users 
            (firebase_uid, email, display_name, photo_url, last_login)
            VALUES (?, ?, ?, ?, ?)
        """, (
            firebase_user['uid'],
            firebase_user.get('email'),
            firebase_user.get('name'),
            firebase_user.get('picture'),
            datetime.now().isoformat()
        ))
        conn.commit()
    except Exception as e:
        print(f"Error storing user info: {e}")
    finally:
        conn.close()

# Handle preflight OPTIONS requests
@app.route('/recommend', methods=['OPTIONS'])
@app.route('/save_favorite', methods=['OPTIONS']) 
@app.route('/favorites', methods=['OPTIONS'])
@app.route('/clear_favorites', methods=['OPTIONS'])
@app.route('/remove_favorite', methods=['OPTIONS'])
@app.route('/user/profile', methods=['OPTIONS'])
@app.route('/user/stats', methods=['OPTIONS'])
@app.route('/auth/verify', methods=['OPTIONS'])
def handle_options():
    response = jsonify({})
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

# New Firebase Authentication Endpoints

@app.route("/auth/verify", methods=["POST"])
@firebase_auth_required
def verify_token():
    """Verify Firebase token and return user info"""
    try:
        firebase_user = request.firebase_user
        
        # Store user info in database
        store_user_info(firebase_user)
        
        user_info = {
            "uid": firebase_user['uid'],
            "email": firebase_user.get('email'),
            "name": firebase_user.get('name'),
            "picture": firebase_user.get('picture'),
            "email_verified": firebase_user.get('email_verified', False)
        }
        
        return jsonify({"success": True, "user": user_info}), 200
        
    except Exception as e:
        print(f"Error verifying token: {e}")
        return jsonify({"success": False, "error": "Token verification failed"}), 401

@app.route("/user/profile", methods=["GET"])
@firebase_auth_required
def get_user_profile():
    """Get user profile information"""
    firebase_uid = request.firebase_user['uid']
    
    conn = sqlite3.connect('user_favorites.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT email, display_name, photo_url, created_at, last_login
            FROM users 
            WHERE firebase_uid = ?
        """, (firebase_uid,))
        
        row = cursor.fetchone()
        
        if row:
            profile = {
                "uid": firebase_uid,
                "email": row[0],
                "display_name": row[1],
                "photo_url": row[2],
                "created_at": row[3],
                "last_login": row[4]
            }
        else:
            # If user not in database, create from Firebase token
            firebase_user = request.firebase_user
            profile = {
                "uid": firebase_uid,
                "email": firebase_user.get('email'),
                "display_name": firebase_user.get('name'),
                "photo_url": firebase_user.get('picture'),
                "created_at": None,
                "last_login": None
            }
            store_user_info(firebase_user)
        
        return jsonify(profile), 200
        
    except Exception as e:
        print(f"Error fetching user profile: {e}")
        return jsonify({"error": "Failed to fetch profile"}), 500
    finally:
        conn.close()

@app.route("/user/stats", methods=["GET"])
@firebase_auth_required
def get_user_stats():
    """Get user statistics (number of favorites, most common mood, etc.)"""
    firebase_uid = request.firebase_user['uid']
    
    conn = sqlite3.connect('user_favorites.db')
    cursor = conn.cursor()
    
    try:
        # Get total favorites count
        cursor.execute("SELECT COUNT(*) FROM user_favorites WHERE firebase_uid = ?", (firebase_uid,))
        total_favorites = cursor.fetchone()[0]
        
        # Get most common mood
        cursor.execute("""
            SELECT mood, COUNT(*) as count 
            FROM user_favorites 
            WHERE firebase_uid = ? AND mood IS NOT NULL
            GROUP BY mood 
            ORDER BY count DESC 
            LIMIT 1
        """, (firebase_uid,))
        
        mood_result = cursor.fetchone()
        most_common_mood = mood_result[0] if mood_result else None
        
        # Get favorite genres (you'd need to add genre tracking)
        # For now, we'll return basic stats
        
        stats = {
            "total_favorites": total_favorites,
            "most_common_mood": most_common_mood,
            "account_created": datetime.now().isoformat()  # You can get this from users table
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        print(f"Error fetching user stats: {e}")
        return jsonify({"error": "Failed to fetch stats"}), 500
    finally:
        conn.close()

# Updated existing endpoints

@app.route("/save_favorite", methods=["POST"])
@firebase_auth_required
def save_favorite():
    data = request.get_json() or {}
    firebase_uid = request.firebase_user['uid']
    movie_id = data.get("id")
    title = data.get("title")
    overview = data.get("overview")
    mood = data.get("mood")
    poster_path = data.get("poster_path")
    watch_providers = data.get("watch_providers", {"flatrate": [], "rent": [], "buy": []})
    release_date = data.get("release_date")
    vote_average = data.get("vote_average")

    if not title or not overview:
        return jsonify({"message": "Missing title or overview."}), 400

    conn = sqlite3.connect('user_favorites.db')
    cursor = conn.cursor()
    
    try:
        # Check if user already has this movie in favorites
        cursor.execute(
            "SELECT id FROM user_favorites WHERE firebase_uid = ? AND movie_id = ?", 
            (firebase_uid, movie_id)
        )
        if cursor.fetchone():
            return jsonify({"message": "Already in favorites."}), 409
        
        # Insert new favorite
        cursor.execute("""
            INSERT INTO user_favorites 
            (firebase_uid, movie_id, title, overview, mood, poster_path, watch_providers, release_date, vote_average)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            firebase_uid, movie_id, title, overview, mood, poster_path, 
            json.dumps(watch_providers), release_date, vote_average
        ))
        
        conn.commit()
        return jsonify({"message": "Favorite saved successfully!"}), 200
        
    except Exception as e:
        print(f"Error saving favorite: {e}")
        return jsonify({"message": "Failed to save favorite."}), 500
    finally:
        conn.close()

@app.route("/recommend", methods=["POST"])
@firebase_auth_optional  # Allow both authenticated and anonymous users
def get_movie_recommendations_api():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        mood = data.get("mood", "happy").lower()
        runtime = data.get("runtime", 90)
        
        recommendations = get_movie_recommendations(mood, runtime)
        
        if not recommendations:
            return jsonify({"movies": [], "message": "No movies found for this mood. Try a different mood or check your internet connection."}), 200
        
        # If user is authenticated, you could personalize recommendations here
        if hasattr(request, 'firebase_user') and request.firebase_user:
            # Add logic to personalize based on user's favorite history
            pass
        
        return jsonify({"movies": recommendations}), 200
        
    except Exception as e:
        return jsonify({"error": "Internal server error", "movies": []}), 500

@app.route("/favorites", methods=["GET"])
@firebase_auth_required
def get_favorites():
    firebase_uid = request.firebase_user['uid']
    
    conn = sqlite3.connect('user_favorites.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT movie_id, title, overview, mood, poster_path, watch_providers, 
                   release_date, vote_average, date_saved
            FROM user_favorites 
            WHERE firebase_uid = ?
            ORDER BY date_saved DESC
        """, (firebase_uid,))
        
        rows = cursor.fetchall()
        favorites = []
        
        for row in rows:
            favorite = {
                "id": row[0],
                "title": row[1],
                "overview": row[2],
                "mood": row[3],
                "poster_path": row[4],
                "watch_providers": json.loads(row[5]) if row[5] else {"flatrate": [], "rent": [], "buy": []},
                "release_date": row[6],
                "vote_average": row[7],
                "date_saved": row[8]
            }
            favorites.append(favorite)
        
        return jsonify(favorites), 200
        
    except Exception as e:
        print(f"Error fetching favorites: {e}")
        return jsonify([]), 500
    finally:
        conn.close()

@app.route("/clear_favorites", methods=["POST"])
@firebase_auth_required  # Fixed: Now requires authentication
def clear_favorites():
    firebase_uid = request.firebase_user['uid']
    
    conn = sqlite3.connect('user_favorites.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM user_favorites WHERE firebase_uid = ?", (firebase_uid,))
        conn.commit()
        return jsonify({"message": "Favorites cleared!"}), 200
    except Exception as e:
        print(f"Error clearing favorites: {e}")
        return jsonify({"message": "Failed to clear favorites."}), 500
    finally:
        conn.close()

@app.route("/remove_favorite", methods=["DELETE"])
@firebase_auth_required
def remove_favorite():
    """Remove a specific movie from favorites"""
    firebase_uid = request.firebase_user['uid']
    data = request.get_json() or {}
    movie_id = data.get("movie_id")
    
    if not movie_id:
        return jsonify({"message": "Movie ID is required"}), 400
    
    conn = sqlite3.connect('user_favorites.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "DELETE FROM user_favorites WHERE firebase_uid = ? AND movie_id = ?", 
            (firebase_uid, movie_id)
        )
        
        if cursor.rowcount == 0:
            return jsonify({"message": "Movie not found in favorites"}), 404
            
        conn.commit()
        return jsonify({"message": "Favorite removed successfully!"}), 200
        
    except Exception as e:
        print(f"Error removing favorite: {e}")
        return jsonify({"message": "Failed to remove favorite."}), 500
    finally:
        conn.close()

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
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=5001, debug=True)