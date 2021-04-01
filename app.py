from bs4 import BeautifulSoup
from bson.objectid import ObjectId
from dotenv import load_dotenv
from flask import Flask, request, render_template, redirect, url_for, jsonify, flash
from flask_googlemaps import GoogleMaps, Map
from flask_pymongo import PyMongo
from html5lib import html5parser
from pymongo import MongoClient
import datetime
import os
import random
import requests

load_dotenv()
MONGODB_USERNAME = os.getenv('MONGODB_USERNAME')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')
MONGODB_DBNAME = 'Cluster1'
google_maps_api_key = os.getenv('google_maps_api_key')

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

@app.route('/add_restaurant', methods=['GET', 'POST'])
def add_restaurant():
    ''' Add restaurant to the database '''
    if request.method == 'POST':
        new_restaurant = {
            'name': request.form.get('restaurant_name'),
            'type': request.form.get('restaurant_type'),
            'ethnicity': request.form.get('restaurant_ethnicity'),
            'price': request.form.get('price'),
            'rating': "No Rating",
            'address': "No Address",
            'image': "No Image"
        }

        result = db.restaurants.insert_one(new_restaurant)
        print(result.inserted_id)
        return render_template('home.html')

    else:
        return render_template('add_restaurant.html')

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

        #Replace spaces with + because the url input expects a + in place of every space
        restaurant_type = food_type.replace(" ", "+")
        restaurant_location = location.replace(" ", "+")

        #Store user info for debugging purposes
        user_info_storage = {}
        user_info_storage['ip'] = js['query']
        user_info_storage['city'] = location
        user_info_storage['search_query'] = restaurant_type
        user_info_storage['time'] = datetime.datetime.now()
        db.user_info_storage.insert_one(user_info_storage)

        print(f"Restaurant Type: {restaurant_type}")
        print(f"Restaurant Location: {restaurant_location}")
        
        try:
            r = requests.get(f"https://www.yelp.com/search?find_desc={restaurant_type}&find_loc={restaurant_location}") #Get html data from page
            print(f"requests.get check: {r}")
            soup = BeautifulSoup(r.content, features="html5lib") #Parse html data with beautifulsoup
        except:
            flash("Error finding restaurants. Please try again!") #Present error if scraping fails for any reason
            render_template('home.html')# Redirects to home page


        #Check if any restaurants are present in the list. If 0, the scraper probably needs updating as site has probably been updated
        #Also used by for loop to know how many restaurants need to be scraped
        restaurants_list = soup.find_all("div", {"class":"container__09f24__21w3G hoverable__09f24__2nTf3 margin-t3__09f24__5bM2Z margin-b3__09f24__1DQ9x padding-t3__09f24__-R_5x padding-r3__09f24__1pBFG padding-b3__09f24__1vW6j padding-l3__09f24__1yCJf border--top__09f24__8W8ca border--right__09f24__1u7Gt border--bottom__09f24__xdij8 border--left__09f24__rwKIa border-color--default__09f24__1eOdn"})
        print(f"Number of restaurants in list: {len(restaurants_list)}")

        #clear db before repopulating it with information from new search
        db.restaurants.drop()
        db.restaurant_info.drop()
        print("collection deleted")

        #iterate through all discovered restaurants in the list and adds information to new_restaurant dictionary
        for i in range(0, len(restaurants_list)):
            new_restaurant = {} #Create empty dictionary to store scraped data

            #Scrape for restaurant name and store with the key, 'name', in dictionary
            try:
                new_restaurant["name"] = restaurants_list[i].find("a", {"class":"css-166la90"}).string
            except:
                new_restaurant["name"] = "Name Unavailable"

            #Scrape for restaurant price range and store with the key, 'price', in dictionary
            try:
                new_restaurant["price"] = restaurants_list[i].find("span", {"class":"priceRange__09f24__2O6le css-xtpg8e"}).string
            except:
                new_restaurant["price"] = "Price Unavailable"


            #Scrape for restaurant thumbnail and store with the key, 'thumbnail', in dictionary
            try:
                image = restaurants_list[i].find("img", {"class":"css-xlzvdl"})
                new_restaurant["image"] = image['src']
            except:
                new_restaurant["image"] = "Image Unavailable"

            #Scrape for restaurant address and store with the key, 'address', in dictionary
            try:
                new_restaurant["address"] = restaurants_list[i].find("span", {"class":"raw__09f24__3Obuy"}).string
            except:
                new_restaurant["address"] = "Address Unavailable"
            
            #Scrape for restaurant rating and store with the key, 'rating', in dictionary
            try:
                #Attempt to find 5 star review
                new_restaurant["rating"] = restaurants_list[i].find("div", {"class":"i-stars__09f24__1T6rz i-stars--regular-5__09f24__2YrSK border-color--default__09f24__1eOdn overflow--hidden__09f24__3z7CX"}).get('aria-label')
            except:
                try:
                    #Attempt to find 4.5 star review
                    new_restaurant["rating"] = restaurants_list[i].find("div", {"class":"i-stars__09f24__1T6rz i-stars--regular-4-half__09f24__1YrPo border-color--default__09f24__1eOdn overflow--hidden__09f24__3z7CX"}).get('aria-label')
                except:
                    try:
                        #Attempt to find 4 star review
                        new_restaurant["rating"] = restaurants_list[i].find("div", {"class":"i-stars__09f24__1T6rz i-stars--regular-4__09f24__2YrSK border-color--default__09f24__1eOdn overflow--hidden__09f24__3z7CX"}).get('aria-label')
                    except:
                        try:
                            #Attempt to find 3.5 star review
                            new_restaurant["rating"] = restaurants_list[i].find("div", {"class":"i-stars__09f24__1T6rz i-stars--regular-3-half__09f24__2YrSK border-color--default__09f24__1eOdn overflow--hidden__09f24__3z7CX"}).get('aria-label')
                        except:
                            try:
                                #Attempt to find 3 star review
                                new_restaurant["rating"] = restaurants_list[i].find("div", {"class":"i-stars__09f24__1T6rz i-stars--regular-3__09f24__2YrSK border-color--default__09f24__1eOdn overflow--hidden__09f24__3z7CX"}).get('aria-label')
                            except:
                                #Return rating unavailable if none of the above ratings are found
                                new_restaurant["rating"] = "Rating Unavailable"

            #Store dictionary information in database. The purpose of this is so that random restaurants can be retrieved later without having to re-scrape every time
            db.restaurants.insert_one(new_restaurant)
            print(new_restaurant)

        #store restaurant information in db
        restaurant_information = {}
        restaurant_information["type"] = food_type
        restaurant_information["location"] = location

        db.restaurant_info.insert_one(restaurant_information)

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
            random_restaurant = restaurant_list[random.randint(0, len(restaurant_list)-1)]
        #displays error if list is empty (happens if scraping failed)
        except:
            flash("Error finding restaurants. Please try again!")
            print("Error: No restaurants in the database")
            return render_template('home.html')

        name = random_restaurant['name']
        price = random_restaurant['price']
        rating = random_restaurant['rating']
        address = random_restaurant['address']
        image = random_restaurant['image']

        #retrieve restaurant information from db
        restaurant_information_list = []
        for item in db.restaurant_info.find():
            restaurant_information_list.append(item)
        
        restaurant_type = restaurant_information_list[0]['type'].title()
        restaurant_location = restaurant_information_list[0]['location'].title()

        #gets restaurant coordinates to be displayed on the map
        restaurant_coordinates = get_coordinates(google_maps_api_key, f"{address} {restaurant_location}")

        context = {
            'name': name,
            'price': price,
            'rating': rating,
            'address': address,
            'image': image,
            'restaurant_type': restaurant_type,
            'restaurant_location': restaurant_location,
            'lat': restaurant_coordinates['lat'],
            'lng': restaurant_coordinates['lng']
        }

        return render_template('show_restaurant.html', **context)

if __name__ == '__main__':
    app.config['ENV'] = 'development'
    app.run(debug=True)