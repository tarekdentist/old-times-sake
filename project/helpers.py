import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
from flask import redirect, render_template, session
from functools import wraps
import requests

# Cloudinary API configuration -- (Enter your own credentials)
cloudinary.config(
    cloud_name="<cloud_name>",
    api_key="<api_key>",
    api_secret="<api_secret>",
    secure=True
)


# Upload the user's image

def upload_image(file):
    upload_result = cloudinary.uploader.upload(file)

    # Optimize delivery by resizing and applying auto-format and auto-quality

    public_id = upload_result.get("public_id")
    optimized_url, _ = cloudinary_url(
        public_id, fetch_format="auto", quality="auto", height=300, width=300, crop="auto", gravity="auto")
    return optimized_url


# Making sure the user is logged in (Same function used in CS50 Finance PS)

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/latest/patterns/viewdecorators/
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)

    return decorated_function


# Using Google Places API to fetch the activities available around the user's location

def get_places(city, country):

    # First API call to get the activities

    api_key = '<api_key>'
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query=activities+in+{city}+{country}&key={api_key}"
    response = requests.get(url)
    data = response.json()

    # Second API call to get the accessibilty info of each activity

    for result in data['results']:
        place_id = result['place_id']
        details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=wheelchair_accessible_entrance&key={api_key}"
        details_response = requests.get(details_url)
        details_data = details_response.json()
        result['wheelchair_accessible_entrance'] = details_data['result'].get(
            'wheelchair_accessible_entrance', None)
    return data


# Rendering the error page with a customized error message and code

def error(message, code=400):
    return render_template("error.html", message=message, code=code), code
