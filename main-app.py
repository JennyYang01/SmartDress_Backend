from flask import Flask
from config import db
from config import gmaps
import datetime
from config import owm
import imp

app = Flask(__name__)
users_collection = db["users"]
weather_collection = db["weather"]
from bson.json_util import dumps
from flask import request, jsonify
import json
import ast

weather_reader = imp.load_source("*", "./weather_reader.py")

@app.route("/api/v1/city/<longitude>/<latitude>", methods=['GET'])
def find_city(longitude, latitude):

    # Geocoding an address
    # geocode_result = gmaps.geocode('1600 Amphitheatre Parkway, Mountain View, CA')
    try:
        # Look up an address with reverse geocoding
        reverse_geocode_result = gmaps.reverse_geocode((float(longitude), float(latitude)))
        return dumps(reverse_geocode_result), 200
    except:
        return "Location not found", 404


@app.route("/api/v1/weather/<city_name>/<country_name>", methods=['GET'])
def find_weather(city_name, country_name):
    # check if there's valid weather info in mongodb cache, return if it's valid
    # otherwise call weather API to
    try:
        weather_in_cache = read_weather_from_db(city_name, country_name)

        if weather_in_cache:
            date_of_weather_in_cache = datetime.datetime.strptime(weather_in_cache["last_update_date"], '%Y-%m-%dT%H:%M:%SZ')
            date_of_weather_current = datetime.datetime.utcnow()
            date_of_weather_difference = date_of_weather_current - date_of_weather_in_cache

            if date_of_weather_difference.seconds >= 3600:
                weather = call_weather_network(city_name, country_name)
                weather = update_weather_in_db(city_name, country_name, weather)
                return dumps(weather), 200
            else:
                return dumps(weather_in_cache), 200
        else:
            weather = call_weather_network(city_name, country_name)
            weather = create_weather_in_db(city_name, country_name, weather)
            return dumps(weather), 200
    except:
        return "Server internal error", 500


def call_weather_network(city_name, country_name):
    full_city_name = weather_reader.url_builder(city_name, country_name)
    weather = weather_reader.data_fetch(full_city_name)
    return weather


def read_weather_from_db(city_name, country_name):
    weather = weather_collection.find_one({"city_name":city_name, "country_name":country_name})
    return weather


def update_weather_in_db(city_name, country_name, weather):
    weather["city_name"] = city_name
    weather["country_name"] = country_name
    weather["last_update_date"] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    body = ast.literal_eval(json.dumps(weather))
    users_collection.update_one({"city_name": city_name, "country_name": country_name}, body)
    return weather


def create_weather_in_db(city_name, country_name, weather):
    weather["city_name"] = city_name
    weather["country_name"] = country_name
    weather["last_update_date"] = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    body = ast.literal_eval(json.dumps(weather))
    weather_collection.insert(body)
    return weather





@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route("/api/v1/users", methods=['POST'])
def create_user():
    try:
        # Create new users
        try:
            body = ast.literal_eval(json.dumps(request.get_json()))
        except:
            # Bad request body is not available
            return "Bad Request", 400

        record_created = users_collection.insert(body)

        # Prepare the response
        if isinstance(record_created, list):
            # Return list of Id of the newly created item
            return jsonify([str(v) for v in record_created]), 201
        else:
            # ReturnId of the newly created item
            return jsonify(str(record_created)), 201

    except:
        # Error while trying to create the resource
        return "Server internal error", 500


@app.route("/api/v1/users", methods=['GET'])
def fetch_users():
    try:
        # Call the json.loads to return a query param dictionary (json object)
        query_params = json.loads(json.dumps(request.args))

        # Check if dictionary is not empty
        if query_params:

            # Try to convert the value to int
            query = {k: int(v) if isinstance(v, str) and v.isdigit() else v for k, v in query_params.items()}
            # Fetch all the record(s)
            records_fetched = users_collection.find(query)

            # Check if the records are found
            if records_fetched.count() > 0:
                # Prepare the response
                return dumps(records_fetched), 200
            else:
                # No records are found
                return "No records found", 404

        # If the dictionary is empty
        else:
            # Return all the records as query string parameters are not available
            if users_collection.find().count() > 0:
                # Prepare response if the users are found
                return dumps (users_collection.find()), 200
            else:
                # Return empty array if no users are found
                return jsonify([]), 200

    except:
        # Error while trying to fetch the resource
        # Add message for debuggin purpose
        return "Server internal error", 500


@app.route("/api/v1/users/<user_id>", methods=['GET'])
def find_user(user_id):
    try:
        record_found = users_collection.find({"User_id": user_id})

        if record_found.count() > 0:
            return dumps(record_found), 200
        else:
            return "No records found", 404

    except:
        return "Server internal error", 500


@app.route("/api/v1/users/<user_id>", methods=['PUT'])
def update_user(user_id):
    try:
        # Get the value which needs to be updated
        try:
            body = ast.literal_eval(json.dumps(request.get_json()))
        except:
            # Bad request as the request body is not available
            return "Bad request", 400

        #Updating the user
        records_updated = users_collection.update_one({"User_id": int(user_id)}, body)

        # Check if resource is updated
        if records_updated.modified_count > 0:
            # Prepare the response as resource is updated successfully
            return "Resource successfully updated", 200
        else:
            # Bad request as the resource is not available to update
            return "No records modified", 404

    except:
        # Error while trying to update the resource
        return "Server internal error", 500


@app.route("/api/v1/users/<user_id>", methods=['DELETE'])
def remove_user(user_id):
    try:
        # Delete the user
        delete_user = users_collection.delete_one({"User_id": int(user_id)})

        if delete_user.deleted_count > 0:
            # Prepare the response
            return "User successfully deleted", 200
        else:
            return "User not found", 404

    except:
        # Error while trying to delete the resource
        return "Server internal error", 500


if __name__ == '__main__':
    app.run()
