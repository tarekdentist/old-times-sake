from cs50 import SQL
from flask import Flask, redirect, render_template, request, session, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from helpers import upload_image, get_places, error, login_required

app = Flask(__name__)


# Session management
app.config["SESSION_PERMANENT"] = True
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Database setup
db = SQL("sqlite:///project.db")

# Ensure content isn't cached for the dynamic content of the site


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = "0"
    response.headers["Pragma"] = "no-cache"
    return response

# Register route


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        username = request.form.get("username")
        gender = request.form.get("gender")
        birthdate = request.form.get("birthdate")
        country = request.form.get("country")
        city = request.form.get("city")

        # Server-side validation in case the user bypasses client-side validation somehow

        if not first_name:
            return error("Please provide a first name", 400)
        elif not last_name:
            return error("Please provide a last name", 400)
        elif not username:
            print("no user name")
            return error("Please provide a username", 400)
        elif not password:
            print("no password")
            return error("Please provide a password", 400)
        elif not confirmation:
            return error("Please confirm your password", 400)
        elif password != confirmation:
            print("no match")
            return error("Passwords don't match", 400)
        elif not gender:
            return error("Please select a gender", 400)
        elif not birthdate:
            return error("please enter your birthday", 400)
        elif not country:
            return error("Please select your country", 400)
        elif not city:
            return error("Please select your city", 400)

        hash = generate_password_hash(password)

        # Age calculation logic by CS50.ai

        birthdate = datetime.strptime(birthdate, "%Y-%m-%d")
        today = datetime.today()
        age = today.year - birthdate.year
        if today < birthdate.replace(year=today.year):
            age -= 1
        if age < 50:
            return error("You need to be older than 50", 400)

        # Collecting the list properly by CS50.ai

        interests = request.form.getlist('interests[]')
        interests_str = ', '.join(interests)

        # Collecting the image and uploading it to Cloudinary API

        image_url = None

        file = request.files['profile_picture']
        if file:
            image_url = upload_image(file)

        try:
            db.execute("INSERT INTO users (first_name, last_name, username, hash, age, gender, country, city, interests, image_url) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       first_name, last_name, username, hash, age, gender, country, city, interests_str, image_url)
        except Exception as e:
            print(e)
            return error("Username already exists", 400)

        rows = db.execute("SELECT id FROM users WHERE username = ?", request.form.get("username"))

        session["user_id"] = rows[0]["id"]

        return redirect("/")

    return render_template("register.html")


# Same login function used in Finance problem set, customized for this application

@app.route("/login", methods=["GET", "POST"])
def login():

    # Forget the user_id
    session.clear()

    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return error("Please provide a username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return error("Please enter your password", 400)

        # Get the username from the database
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return error("Password or username is incorrect", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("login.html")


# Logging the user out by clearing the session

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# Homepage


@app.route("/")
def index():
    return render_template("index.html")


# Connect route (allow the user to view other users nearby and send connect requests to them)

@app.route("/connect", methods=["GET", "POST"])
@login_required
def connect():

    # Get the country and city of the user to filter out other users

    sender_info = db.execute("SELECT country, city FROM users WHERE id = ?", session['user_id'])
    sender_country = sender_info[0]['country']
    sender_city = sender_info[0]['city']

    # Get other users based on the country or city and excluding the current user

    receivers_country = db.execute(
        """
        SELECT id, first_name, last_name, username, age, gender, image_url, interests, city
        FROM users
        WHERE id != ?
        AND country = ?
        AND id NOT IN (
            SELECT receiver_id
            FROM connections
            WHERE sender_id = ?
        )
        """,
        session['user_id'], sender_country, session['user_id']
    )

    receivers_city = db.execute(
        """
        SELECT id, first_name, last_name, username, age, gender, image_url, interests, city
        FROM users
        WHERE id != ?
        AND city = ?
        AND id NOT IN (
            SELECT receiver_id
            FROM connections
            WHERE sender_id = ?
        )
        """,
        session['user_id'], sender_city, session['user_id']
    )

    # Sending the connect request

    if request.method == "POST":

        # Get the id of the receiver

        receiver_id = request.form.get('receiver_id')

        # Insert the request into the database

        db.execute("INSERT INTO connections (sender_id, receiver_id, status) VALUES (?, ?, ?)",
                   session['user_id'], receiver_id, 'pending')

    return render_template("connect.html", receivers_country=receivers_country, receivers_city=receivers_city)


# Requests route (showing the user the connect requests they received)

@app.route("/requests", methods=["GET", "POST"])
@login_required
def requests():

    # Getting the requests from the database using nested query

    requests = db.execute(
        """
        SELECT
            users.id,
            users.first_name,
            users.last_name,
            users.age,
            users.gender,
            users.country,
            users.city,
            users.image_url,
            users.interests,
            connections.request_id
        FROM users
        JOIN connections ON users.id = connections.sender_id
        WHERE connections.receiver_id = ?
        AND connections.status = ?
        """,
        session['user_id'], 'pending'
    )

    if request.method == "POST":

        # Get the id of the request

        request_id = request.form.get("request_id")
        action = request.form.get("action")

        # Update the connections table based on the button the user clicks on

        if action == "accept":
            db.execute("UPDATE connections SET status = ? WHERE request_id =?",
                       'accepted', request_id)
        elif action == "reject":
            db.execute("UPDATE connections SET status = ? WHERE request_id =?",
                       'rejected', request_id)

    return render_template("requests.html", requests=requests)


# Activities route (showing the activities in the user's city using Google Places API and allowing them to send invites to their friends)

@app.route("/activities", methods=["GET", "POST"])
@login_required
def activities():

    # Getting the user's friends from the database

    users = db.execute(
        """
        SELECT username, first_name, last_name, id
        FROM users
        WHERE id IN (
            SELECT receiver_id
            FROM connections
            WHERE status = ? AND sender_id = ?
        )
        OR id IN (
            SELECT sender_id
            FROM connections
            WHERE status = ? AND receiver_id = ?
        )
        """,
        'accepted', session['user_id'],
        'accepted', session['user_id']
    )

    # Handling sending the invite requst and adding it to the database

    if request.method == "POST":

        place_name = request.form.get('place_name')
        user_ids = request.form.getlist('user_ids[]')

        if user_ids:
            for user_id in user_ids:
                if user_id:
                    db.execute("INSERT INTO invitations (sender_id, receiver_id, place_name) VALUES (?, ?, ?)",
                               session['user_id'], int(user_id), place_name)

    home = db.execute("SELECT city, country FROM users WHERE id = ?", session['user_id'])
    city = home[0]['city']
    country = home[0]['country']

    # Fetching the activities from Google Places API

    places_data = get_places(city, country)

    if not places_data:
        return error("An error occured while loading activities. Please try again later", 400)

    # Filtering through the activities to show the ones that are suitable for the elderly

    keywords = ['park', 'tourist_attraction', 'garden', 'theater', 'museum', 'cinema',
                'cafe', 'library', 'gallery', 'community center', 'mall', 'book', 'historical']
    excluded_keywords = ['ride', 'rides', 'kingdom', 'kids',
                         'kid', 'children', 'amusement', 'play', 'magic']
    elderly_places = []

    added_place_ids = set()

    for result in places_data['results']:

        # Showing the accessibility info in a user-friendly way

        if result['wheelchair_accessible_entrance'] is True:
            result['wheelchair_accessible_entrance'] = "Wheelchair Accessible"
        else:
            result['wheelchair_accessible_entrance'] = "Not Specified"

        # Error handling in case the API does not return a photo because it causes an internal server error sometimes

        if 'photos' not in result:
            result['photos'] = None

        # Filtering

        for keyword in keywords:
            for type in result['types']:
                if keyword in result['name'].lower() or keyword in type.lower():
                    # Check if the place id is not already in the list to avoid dublicates since name and type could be the same
                    if result['place_id'] not in added_place_ids:
                        elderly_places.append(result)
                        added_place_ids.add(result['place_id'])
                break

        # Excluding places from results in case they have certain keywords (Used ChatGPT to implement my logic).

        filtered_places = []
        for place in elderly_places:
            exclude_place = False
            for excluded_keyword in excluded_keywords:
                if excluded_keyword in place['name'].lower() or excluded_keyword in ' '.join(place['types']).lower():
                    exclude_place = True
                    break
            if not exclude_place:
                filtered_places.append(place)

        print(filtered_places)
    return render_template("activities.html", city=city, country=country, places=filtered_places, users=users)


# Invitation route (showing the user the invitation requests they received)

@app.route("/invitations", methods=["GET", "POST"])
@login_required
def invitations():

    # Getting the pending invitations from the database

    invitations = db.execute(
        """
        SELECT
            users.id,
            users.username,
            users.first_name,
            users.last_name,
            users.image_url,
            invitations.invitation_id,
            invitations.place_name
        FROM users
        JOIN invitations ON users.id = invitations.sender_id
        WHERE invitations.receiver_id = ?
        AND invitations.status = ?
        """,
        session['user_id'], 'Pending'
    )

    if request.method == "POST":

        # Get the id of the invitation

        invitation_id = request.form.get("invitation_id")
        action = request.form.get("action")

        # Update the connections table based on the button the user clicks on

        if action == "accept":
            db.execute("UPDATE invitations SET status = ? WHERE invitation_id =?",
                       'accepted', invitation_id)
        elif action == "reject":
            db.execute("UPDATE invitations SET status = ? WHERE invitation_id =?",
                       'rejected', invitation_id)

    return render_template("invitations.html", invitations=invitations)


# Friends route (showing the user's friends and allowing them to send messages)

@app.route("/friends", methods=["GET", "POST"])
@login_required
def friends():

    # Handling GET request to display friends

    friends = db.execute(
        """
        SELECT id, username, first_name, last_name, age, gender, city, country, image_url, interests
        FROM users
        WHERE id IN (
            SELECT receiver_id
            FROM connections
            WHERE status = ? AND sender_id = ?
        )
        OR id IN (
            SELECT sender_id
            FROM connections
            WHERE status = ? AND receiver_id = ?
        )
        """,
        'accepted', session['user_id'],
        'accepted', session['user_id']
    )

    # Handling POST request to send messages

    if request.method == "POST":
        message = request.form.get("message")
        friend_id = request.form.get("friend_id")

        # Insert the message into the database
        db.execute(
            "INSERT INTO messages (sender_id, receiver_id, message) VALUES (?, ?, ?)",
            session['user_id'], friend_id, message
        )

        return jsonify({"success": True})

    return render_template("friends.html", friends=friends)


# Messages route (showing the user the messages they received and allowing them to reply)

@app.route("/messages", methods=["GET", "POST"])
@login_required
def messages():

    # Getting the messages from the database in a descending order

    messages = db.execute(
        """
        SELECT
            users.id,
            users.username,
            users.first_name,
            users.last_name,
            users.image_url,
            messages.message_id,
            messages.message,
            messages.timestamp
        FROM users
        JOIN messages ON users.id = messages.sender_id
        WHERE messages.receiver_id = ?
        ORDER BY messages.message_id DESC
        """,
        session['user_id']
    )

    # Handling sending the reply

    if request.method == "POST":

        message = request.form.get("message")
        friend_id = request.form.get("friend_id")

        # Insert the message into the database

        db.execute(
            "INSERT INTO messages (sender_id, receiver_id, message) VALUES (?, ?, ?)",
            session['user_id'], friend_id, message
        )

        return jsonify({"success": True})

    return render_template("messages.html", messages=messages)


# Notification route (showing the user whether their invitations were accepted or rejected)

@app.route("/notifications")
@login_required
def notifications():

    # Getting the notifications from the database

    notifications = db.execute(
        """
        SELECT
            users.id,
            users.username,
            users.first_name,
            users.last_name,
            users.image_url,
            invitations.invitation_id,
            invitations.status,
            invitations.place_name
        FROM users
        JOIN invitations ON users.id = invitations.sender_id
        WHERE invitations.sender_id = ? AND (invitations.status = 'accepted' OR invitations.status = 'rejected')
        ORDER BY invitations.invitation_id DESC
        """,
        session['user_id']
    )

    return render_template("notifications.html", notifications=notifications)


# Profile route (showing the user their profile details and allowing them to change profile picture and password)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():

    # Getting the new picture and uploading to it Cloudinary API

    if request.method == "POST":
        file = request.files['profile_picture']
        image_url = upload_image(file)
        db.execute("UPDATE users SET image_url = ? WHERE id = ?", image_url, session['user_id'])
        return redirect("/profile")

    # Showing the user's info

    rows = db.execute(
        "SELECT first_name, last_name, username, image_url, country, city FROM users WHERE id = ?", session["user_id"])
    username = rows[0]['username']
    image_url = rows[0]['image_url']
    country = rows[0]['country']
    city = rows[0]['city']
    first_name = rows[0]['first_name']
    last_name = rows[0]['last_name']

    return render_template("profile.html", first_name=first_name, last_name=last_name, username=username, image_url=image_url, country=country, city=city)


# Change route (for changing the user's password)

@app.route("/change", methods=["GET", "POST"])
@login_required
def change():
    if request.method == "POST":
        current_pass = request.form.get("current_pass")
        new_pass = request.form.get("password")
        confirmation = request.form.get("confirmation")
        db_pass = db.execute("SELECT hash FROM users WHERE id = ?", session["user_id"])
        hashed_pass = db_pass[0]['hash']

        # Error handling to ensure the user enters the passwords

        if not current_pass or not new_pass or not confirmation:
            return error("Please fill the empty field", 403)

        # Ensure the password the user enters matches the one in the database

        if not check_password_hash(hashed_pass, current_pass):
            return error("Wrong Password", 403)

        # Ensure password confirmation is correct

        elif new_pass != confirmation:
            return error("Please confirm your password again", 403)

        # Hasing the new password and updating the database

        else:
            hash_new_pass = generate_password_hash(new_pass)
            db.execute("UPDATE users SET hash = ? WHERE id = ?", hash_new_pass, session['user_id'])
            return redirect("/")

    return render_template("change.html")
