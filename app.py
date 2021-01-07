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

if __name__ == '__main__':
    app.config['ENV'] = 'development'
    app.run(debug=True)