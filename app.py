from bs4 import BeautifulSoup
from bson.objectid import ObjectId
from dotenv import load_dotenv
from flask import Flask, request, render_template, redirect, url_for, jsonify, flash
from flask_googlemaps import GoogleMaps, Map
from flask_pymongo import PyMongo
from html5lib import html5parser
from pymongo import MongoClient
from yelpapi import YelpAPI
import datetime, os, random, requests

load_dotenv()
MONGODB_USERNAME = os.getenv('MONGODB_USERNAME')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')
MONGODB_DBNAME = 'RandomRestaurantPicker'
google_maps_api_key = os.getenv('google_maps_api_key')
yelp_api = YelpAPI(os.getenv('yelp_api_key'), timeout_s = 3.0) #Initialize Yelp api

app = Flask(__name__) #Instantiate Flask app
GoogleMaps(app, key=google_maps_api_key) #Instantiate GoogleMaps api
app.secret_key = os.urandom(24)

client = MongoClient(f"mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@cluster0.1uw6i.mongodb.net/{MONGODB_DBNAME}?retryWrites=true&w=majority") #Instantiate mongodb
db = client[MONGODB_DBNAME]

def get_coordinates(API_KEY, address_text):
    ''' google maps api to get coordinates from address '''
    response = requests.get(
        "https://maps.googleapis.com/maps/api/geocode/json?address="
        + address_text
        + "&key="
        + API_KEY
    ).json()
    return response["results"][0]["geometry"]["location"]

@app.route('/')
def homepage():
    ''' Restaurant picker homepage '''
    return render_template('home.html')

@app.route('/about')
def about():
    ''' About page '''
    return render_template('about.html')

@app.route('/search_restaurants', methods=['GET', 'POST'])
def search_restaurants():
    ''' Search for new restaurants to add to databse '''
    if request.method == 'POST':
        location = ''

        #checks if ip address is being forwarded. depends if running locally or deployed
        try:
            #Method of getting user's ip if running locally
            if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
                response = requests.get("http://ip-api.com/json")
                js = response.json()
                location = js['city']
                print(f"User's IP address: {js['query']}. (Not forwarded)")
                print(f"Location based on ip address: {location}. (Not forwarded)")

            #Method of getting user's ip if running deployed on heroku
            else:
                print(f"User's IP address: {request.environ['HTTP_X_FORWARDED_FOR']}. (Forwarded)")
                ip = request.environ['HTTP_X_FORWARDED_FOR']
                response = requests.get(f"http://ip-api.com/json/{ip}")
                js = response.json()
                location = js['city']
                print(f"Location based on ip address: {location}. (Forwarded)")

        except:
            pass

        #Uses location retrieved from above if user wants to automatically search by their location
        if request.form['button'] == 'Search using my location!':
            food_type = request.form.get('food_type')

        #Uses user entered location if user wants to search by input location
        else:
            food_type = request.form.get('food_type')
            location = request.form.get('location')

            #Ensures user enters a location if they choose the 'enter location manually' option
            if request.form.get('location') == '':
                flash("Please enter a location!")
                return render_template('search_restaurants.html')

            else:
                pass

        #Store user info for debugging purposes
        user_info_storage = {}
        user_info_storage['ip'] = js['query']
        user_info_storage['city'] = location
        user_info_storage['search_query'] = food_type
        user_info_storage['time'] = datetime.datetime.now()
        db.user_info_storage.insert_one(user_info_storage)

        #clear db before repopulating it with information from new search
        db.restaurants.drop()
        db.restaurant_info.drop()

        result = yelp_api.search_query(term = food_type, location = location)
        restaurant_info = result['businesses']

        for restaurant in restaurant_info:
            new_restaurant = {}

            new_restaurant['name'] = restaurant['name']
            try:
                new_restaurant['price'] = restaurant['price']
            except:
                new_restaurant['price'] = 'N/A'
            new_restaurant['image'] = restaurant['image_url']
            new_restaurant['address'] = f"{restaurant['location']['display_address'][0]} {restaurant['location']['display_address'][1]}"
            new_restaurant['rating'] = restaurant['rating']
            new_restaurant['user_entered_type'] = food_type
            new_restaurant['user_entered_location'] = location

            db.restaurants.insert_one(new_restaurant)

        return redirect(url_for('show_restaurants'))

    else:
        return render_template('search_restaurants.html')

@app.route('/show_restaurants', methods=['GET', 'POST'])
def show_restaurants():
    ''' Displays restaurants in the database/displays random restaurant? '''
    if request.method == 'POST':

        if request.form['button'] == 'Start Over':
            return redirect(url_for('search_restaurants'))
        
        else:
            return redirect(url_for('search_restaurants'))


    else:
        #adds all restaurants in the db to restaurant_list
        restaurant_list = []
        for item in db.restaurants.find():
            restaurant_list.append(item)

        #chooses a random restaurant from the list to be displayed
        random_restaurant = ''
        try:
            random_restaurant = restaurant_list[random.randint(0, len(restaurant_list) - 1)]
        #displays error if list is empty (happens if scraping failed)
        except:
            flash("Error finding restaurants. Please try again!")
            print("Error: No restaurants in the database")
            return render_template('home.html')

        #gets restaurant coordinates to be displayed on the map
        restaurant_coordinates = get_coordinates(google_maps_api_key, f"{random_restaurant['address']} {random_restaurant['user_entered_location']}")

        context = {
            'name': random_restaurant['name'],
            'price': random_restaurant['price'],
            'rating': random_restaurant['rating'],
            'address': random_restaurant['address'],
            'image': random_restaurant['image'],
            'restaurant_type': random_restaurant['user_entered_type'],
            'restaurant_location': random_restaurant['user_entered_location'],
            'lat': restaurant_coordinates['lat'],
            'lng': restaurant_coordinates['lng']
        }

        return render_template('show_restaurant.html', **context)

if __name__ == '__main__':
    app.config['ENV'] = 'development'
    app.run(debug=True)