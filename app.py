from flask import Flask, request, render_template
from flask_pymongo import PyMongo
from pymongo import MongoClient
from dotenv import load_dotenv
import os

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

if __name__ == '__main__':
    app.config['ENV'] = 'development'
    app.run(debug=True)