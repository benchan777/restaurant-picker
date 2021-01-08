from flask import Flask, request, render_template, redirect, url_for
from flask_pymongo import PyMongo
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup
import requests
from html5lib import html5parser
from bson.objectid import ObjectId
import random

load_dotenv()
MONGODB_USERNAME = os.getenv('MONGODB_USERNAME')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')
MONGODB_DBNAME = 'Cluster1'

app = Flask(__name__)

client = MongoClient(f"mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@cluster0.1uw6i.mongodb.net/{MONGODB_DBNAME}?retryWrites=true&w=majority")
db = client[MONGODB_DBNAME]

global_restaurant_type = ''
global_restaurant_location = ''

@app.route('/')
def homepage():
    ''' Restaurant picker homepage '''
    return render_template('home.html')

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
        api_key = os.getenv('api_key')
        try:
            response = requests.get("http://ip-api.com/json")
            js = response.json()
            location = js['city']
            print(location)
        except:
            pass

        food_type = request.form.get('food_type')
        if request.form.get('location') == '':
            pass
        else:
            location = request.form.get('location')

        restaurant_type = food_type.replace(" ", "+")
        restaurant_location = location.replace(" ", "+")

        print(restaurant_type)
        print(restaurant_location)
        
        r = requests.get(f"https://www.yelp.com/search?find_desc={restaurant_type}&find_loc={restaurant_location}")
        soup = BeautifulSoup(r.content, features="html5lib")

        # r = requests.get(f"https://api.scrapingdog.com/scrape?api_key={api_key}&url=https://www.yelp.com/search?find_desc={restaurant_type}&find_loc={restaurant_location}").text
        # soup = BeautifulSoup(r, 'html.parser')

        # url=f"https://api.scrapingdog.com/scrape?api_key={api_key}&url=https://www.yelp.com/search?find_desc={restaurant_type}&find_loc={restaurant_location}"
        # prox=f"http://scrapingdog:{api_key}@proxy.scrapingdog.com:8081"
        # proxyDict = {"http"  : prox, "https":prox}
        # r = requests.get(url, proxies=proxyDict).text
        # soup = BeautifulSoup(r, 'html.parser')

        restaurants_list = soup.find_all("div", {"class":"container__09f24__21w3G hoverable__09f24__2nTf3 margin-t3__09f24__5bM2Z margin-b3__09f24__1DQ9x padding-t3__09f24__-R_5x padding-r3__09f24__1pBFG padding-b3__09f24__1vW6j padding-l3__09f24__1yCJf border--top__09f24__1H_WE border--right__09f24__28idl border--bottom__09f24__2FjZW border--left__09f24__33iol border-color--default__09f24__R1nRO"})
        print(f"Number of restaurants in list: {len(restaurants_list)}")

        db.restaurants.drop()
        print("collection deleted")

        for i in range(0, len(restaurants_list)):
            new_restaurant = {}

            try:
                new_restaurant["name"] = restaurants_list[i].find("a", {"class":"link__09f24__1kwXV link-color--inherit__09f24__3PYlA link-size--inherit__09f24__2Uj95"}).string
            except:
                new_restaurant["name"] = "No Name"

            try:
                new_restaurant["price"] = restaurants_list[i].find("span", {"class":"text__09f24__2tZKC priceRange__09f24__2O6le text-color--black-extra-light__09f24__38DtK text-align--left__09f24__3Drs0 text-bullet--after__09f24__1MWoX"}).string
            except:
                new_restaurant["price"] = "No Price"
            
            try:
                new_restaurant["rating"] = restaurants_list[i].find("div", {"class":"i-stars__09f24__1T6rz i-stars--regular-4__09f24__2YrSK border-color--default__09f24__R1nRO overflow--hidden__09f24__3u-sw"}).get('aria-label')
            except:
                try:
                    new_restaurant["rating"] = restaurants_list[i].find("div", {"class":"i-stars__09f24__1T6rz i-stars--regular-4-half__09f24__1YrPo border-color--default__09f24__R1nRO overflow--hidden__09f24__3u-sw"}).get('aria-label')
                except:
                    try:
                        new_restaurant["rating"] = restaurants_list[i].find("div", {"class":"i-stars__09f24__1T6rz i-stars--regular-3-half__09f24__dpRnb border-color--default__09f24__R1nRO overflow--hidden__09f24__3u-sw"}).get('aria-label')
                    except:
                        try:
                            new_restaurant["rating"] = restaurants_list[i].find("div", {"class":"i-stars__09f24__1T6rz i-stars--regular-3__09f24__Xlhbn border-color--default__09f24__R1nRO overflow--hidden__09f24__3u-sw"}).get('aria-label')
                        except:
                            try:
                                new_restaurant["rating"] = restaurants_list[i].find("div", {"class":"i-stars__09f24__1T6rz i-stars--regular-5__09f24__N5JxY border-color--default__09f24__R1nRO overflow--hidden__09f24__3u-sw"}).get('aria-label')
                            except:
                                new_restaurant["rating"] = "No Rating"

            try:
                image = restaurants_list[i].find("img", {"class":"photo-box-img__09f24__3F3c5"})
                new_restaurant["image"] = image['src']
            except:
                new_restaurant["image"] = "No Image"

            try:
                new_restaurant["address"] = restaurants_list[i].find("span", {"class":"raw__09f24__3Obuy"}).string
            except:
                new_restaurant["image"] = "No Address"

            db.restaurants.insert_one(new_restaurant)
            print(new_restaurant)

        global global_restaurant_type
        global_restaurant_type = restaurant_type.replace("+", " ")
        global global_restaurant_location
        global_restaurant_location = restaurant_location.replace("+", " ")

        return redirect(url_for('show_restaurants'))

    else:
        return render_template('search_restaurants.html')

@app.route('/show_restaurants', methods=['GET', 'POST'])
def show_restaurants():
    ''' Displays restaurants in the database/displays random restaurant? '''
    if request.method == 'POST':
        return redirect(url_for('search_restaurants'))

    else:
        restaurant_list = []
        for item in db.restaurants.find():
            restaurant_list.append(item)

        random_restaurant = ''
        try:
            random_restaurant = restaurant_list[random.randint(0, len(restaurant_list)-1)]
        except:
            return render_template('home.html')

        name = random_restaurant['name']
        price = random_restaurant['price']
        rating = random_restaurant['rating']
        address = random_restaurant['address']
        image = random_restaurant['image']

        context = {
            'name': name,
            'price': price,
            'rating': rating,
            'address': address,
            'image': image,
            'restaurant_type': global_restaurant_type,
            'restaurant_location': global_restaurant_location
        }

        return render_template('show_restaurant.html', **context)

if __name__ == '__main__':
    app.config['ENV'] = 'development'
    app.run(debug=True)