from flask import Flask, request, render_template
from flask_pymongo import PyMongo
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup
import requests
from html5lib import html5parser

load_dotenv()
MONGODB_USERNAME = os.getenv('MONGODB_USERNAME')
MONGODB_PASSWORD = os.getenv('MONGODB_PASSWORD')
MONGODB_DBNAME = 'Cluster1'

app = Flask(__name__)

client = MongoClient(f"mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@cluster0.1uw6i.mongodb.net/{MONGODB_DBNAME}?retryWrites=true&w=majority")
db = client[MONGODB_DBNAME]

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
            'price': request.form.get('price')
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
        food_type = request.form.get('food_type')
        location = request.form.get('location')

        restaurant_type = food_type.replace(" ", "+")
        restaurant_location = location.replace(" ", "+")
        
        r = requests.get(f"https://www.yelp.com/search?find_desc={restaurant_type}&find_loc={restaurant_location}%2C+CA")
        soup = BeautifulSoup(r.content, features="html5lib")
        restaurants_list = soup.find_all("div", {"class":"container__09f24__21w3G hoverable__09f24__2nTf3 margin-t3__09f24__5bM2Z margin-b3__09f24__1DQ9x padding-t3__09f24__-R_5x padding-r3__09f24__1pBFG padding-b3__09f24__1vW6j padding-l3__09f24__1yCJf border--top__09f24__1H_WE border--right__09f24__28idl border--bottom__09f24__2FjZW border--left__09f24__33iol border-color--default__09f24__R1nRO"})
        print(len(restaurants_list))

        for i in range(0, len(restaurants_list)):
            l = {}

            try:
                l["name"] = restaurants_list[i].find("a", {"class":"link__09f24__1kwXV link-color--inherit__09f24__3PYlA link-size--inherit__09f24__2Uj95"}).string
            except:
                l["name"] = None

            try:
                l["price"] = restaurants_list[i].find("span", {"class":"text__09f24__2tZKC priceRange__09f24__2O6le text-color--black-extra-light__09f24__38DtK text-align--left__09f24__3Drs0 text-bullet--after__09f24__1MWoX"}).string
            except:
                l["price"] = None
            
            try:
                l["rating"] = restaurants_list[i].find("div", {"class":"i-stars__09f24__1T6rz i-stars--regular-4__09f24__2YrSK border-color--default__09f24__R1nRO overflow--hidden__09f24__3u-sw"}).get('aria-label')
            except:
                l["rating"] = "No Rating"

            db.restaurants.insert_one(l)
            print(l)

        return render_template('home.html')

    else:
        return render_template('search_restaurants.html')

if __name__ == '__main__':
    app.config['ENV'] = 'development'
    app.run(debug=True)