from pymongo import MongoClient
import googlemaps
import pyowm

client = MongoClient('mongodb://localhost:27017/')
db = client['Dress-for-the-Weather']

gmaps = googlemaps.Client(key="AIzaSyAnET_JpERI4Vj4lWEVs5ZxPTA1TQc7Rsk")

owm = pyowm.OWM("8563c12cffdbe680251f28b2d31c3b82")

user_api_key = "8563c12cffdbe680251f28b2d31c3b82"

weather_api_url = 'http://api.openweathermap.org/data/2.5/weather?q='