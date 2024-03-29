#!/usr/bin/python3

'''
UNSW COMP9321 19T3
Assignment 2
Team Data Analysis Towards Abbreviation
Members (In order of Last Name)
Genyuan Liang z5235682
Jiasi Lu z5122462
Yefeng Niu z5149500
Haiyan Xu z5135077
Xiaowei Zhou z5108173
Environment:
Python 3.7
'''
import pandas as pd
import jwt
import json
from functools import wraps
from flask import Flask
from flask import request
from flask_restplus import Resource, Api, abort
from flask_restplus import fields
from flask_restplus import inputs
from flask_restplus import reqparse
from sqlalchemy import create_engine
from time import time
from itsdangerous import JSONWebSignatureSerializer, BadSignature, SignatureExpired
import re

from prediction import *

from user import User

app = Flask(__name__)
api = Api(app, authorizations={
    'API-KEY': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'AUTH-TOKEN'
    },
},
          security='API-KEY',
          default="Properties",  # Default namespace
          title="Property Dataset",  # Documentation Title
          description="Property hosting system along with price prediction, property return estimate")  # Documentation Description

# ============ Some Global variable ==============
property_type_list = ['All', 'Aparthotel', 'Apartment', 'Barn', 'Bed and breakfast',
                      'Boat', 'Boutique hotel', 'Bungalow', 'Cabin', 'Camper/rv',
                      'Campsite', 'Casa particular(cuba)', 'Castle', 'Cave', 'Chalet',
                      'Condominium', 'Cottage', 'Dome house', 'Earth house', 'Farm stay',
                      'Guest suite', 'Guesthouse', 'Heritage hotel(India)', 'Hostel',
                      'Hotel', 'House', 'Hut', 'Island', 'Loft', 'Nature lodge',
                      'Other', 'Resort', 'Serviced apartment', 'Tent', 'Tiny house', 'Tipi',
                      'Townhouse', 'Train', 'Treehouse', 'Villa', 'Yurt']

room_type_list = ['All', 'Private room', 'Entire home/apt', 'Shared room']


# ============== For Authentication ===============
class AuthenticationToken:
    def __init__(self, secret_key, expires_in):
        self._secret_key = secret_key
        self._expires_in = expires_in

    def generate_token(self, user):
        info = {
            'username': user['username'],
            'role': user['role'],
            'creation_time': time()
        }
        #print(info)
        return jwt.encode(info, self._secret_key, algorithm='HS256')

    def validate_token(self, token):
        info = jwt.decode(token, self._secret_key, algorithm='HS256')
        # check whether the token is expire or not
        if time() - info['creation_time'] > self._expires_in:
            raise SignatureExpired("The Token has been expired; get a new token")
        return info['username']


SECRET_KEY = "A SECRET KEY; USUALLY A VERY LONG RANDOM STRING"
expires_in = 1800
auth = AuthenticationToken(SECRET_KEY, expires_in)


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('AUTH-TOKEN')
        if not token:
            abort(401, 'Authentication token is missing')
        try:
            user = auth.validate_token(token)
        except Exception as e:
            print(e)
            abort(401, e)
        return f(*args, **kwargs)

    return decorated


# ================== Parsers ====================
credential_parser = reqparse.RequestParser()
credential_parser.add_argument('username', type=str)
credential_parser.add_argument('password', type=str)

search_condition_parser = reqparse.RequestParser()
search_condition_parser.add_argument('min_price', type=int, default=0)
search_condition_parser.add_argument('max_price', type=int, default=0)
search_condition_parser.add_argument('suburb', type=str, default='All')
search_condition_parser.add_argument('property_type', choices=property_type_list, default='All')
search_condition_parser.add_argument('room_type', choices=room_type_list, default='All')
search_condition_parser.add_argument('accommodates', type=int, default=0)
search_condition_parser.add_argument('cleanliness rating weight', type=float, default=1)
search_condition_parser.add_argument('location rating weight', type=float, default=1)
search_condition_parser.add_argument('communication rating weight', type=float, default=1)
search_condition_parser.add_argument('order_by', choices=['price', 'total_rating', 'customized_rating'],
                                     default='price')
search_condition_parser.add_argument('sorting', choices=['ascending', 'descending'], default='ascending')
search_condition_parser.add_argument('page', type=int, default=1)

prediction_parser = reqparse.RequestParser()
prediction_parser.add_argument('date', type=str)

# =================== Models ====================
property_model = api.model('Property', {
    'name': fields.String,
    'host_neighbourhood': fields.String,
    'city': fields.String,
    'property_type': fields.String,
    'room_type': fields.String,
    'accommodates': fields.Integer,
    'bathrooms': fields.Integer,
    'bedrooms': fields.Integer,
    'beds': fields.Integer,
    'amenities': fields.String,
    'price': fields.Float,
    'security_deposit': fields.Float,
    'cleaning_fee': fields.Float,
    'guests_included': fields.Integer
})

prefs_model = api.model('Prefs', {
    'cleanliness': fields.Float,
    'location': fields.Float,
    'communication': fields.Float
})

register_model = api.model('Register', {
    'username': fields.String,
    'email': fields.String,
    'password': fields.String,
    'repeat_password': fields.String
})

password_change_model = api.model('Password_Change', {
    'old_password': fields.String,
    'new_password': fields.String,
    'repeat_new_password': fields.String
})

email_change_model = api.model('Email_Change', {
    'new_email': fields.String,
})

@api.route('/token')
class Token(Resource):
    @api.response(200, 'Successful')
    @api.response(401, 'Auth failed')
    @api.doc(description="Generates an authentication token with new username and password")
    @api.expect(credential_parser, validate=True)
    def get(self):
        args = credential_parser.parse_args()
        username = args.get('username')
        password = args.get('password')
        # validate account
        user = User.login(conn, username, password)
        if user is None:
            # login failed
            return {"message": "authorization has been refused for those credentials."}, 401
        else:
            token = auth.generate_token(user).decode()
            #print(jwt.decode(token, SECRET_KEY, algorithm='HS256'))
            return {'token': auth.generate_token(user).decode()}


@api.route('/register')
class Register(Resource):
    @api.response(200, 'Successful')
    @api.response(400, 'Registration Failed')
    @api.doc(description="Generates a new user with new username, email and password")
    @api.expect(register_model, validate=True)
    def post(self):
        register_info = request.json
        username = register_info['username']
        email = register_info['email']
        password = register_info['password']
        repeat_password = register_info['repeat_password']
        if password != repeat_password:
            return {"message": "Password not match."}, 400
        regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
        if not re.search(regex, email):
            return {"message": "Invalid Email Address."}, 400
        if User.is_username_exists(conn, username):
            return {"message": "username exists."}, 400
        User(username, email, password).commit(conn)
        User.set_prefs(conn, username)
        return {"message": "Register Successfully"}, 200

@api.route('/user/prefs')
class Prefernces(Resource):
    @api.response(200, 'Update User Preferences Success')
    @api.response(400, 'Validation Error')
    @api.doc(description="Update preferences on different aspect of ratings")
    @api.expect(prefs_model, validate=True)
    @requires_auth
    def post(self):
        token = request.headers.get('AUTH-TOKEN')
        user = jwt.decode(token, SECRET_KEY, algorithm='HS256')
        prefs = request.json
        if prefs['cleanliness'] < 0:
            return {"message": "Invalid cleanliness weight"}, 400
        if prefs['location'] < 0:
            return {"message": "Invalid location weight"}, 400
        if prefs['communication'] < 0:
            return {"message": "Invalid communication weight"}, 400
        User.set_prefs(conn, user['username'], cleanliness=prefs['cleanliness'], location=prefs['location'], communication = prefs['communication'])
        return {"message": "User preferences for {} has been updated".format(user['username'])}, 200

@api.route('/user/change_password')
class ChangePassword(Resource):
    @api.response(200, 'Update Password Success')
    @api.response(400, 'Password Update Error')
    @api.doc(description="Change existing password of user")
    @api.expect(password_change_model, validate=True)
    @requires_auth
    def post(self):
        token = request.headers.get('AUTH-TOKEN')
        user = jwt.decode(token, SECRET_KEY, algorithm='HS256')
        pwd_info = request.json
        old_password = pwd_info['old_password']
        new_password = pwd_info['new_password']
        repeat_new_password = pwd_info['repeat_new_password']
        username = user['username']
        current_user = User.get_user_object(conn, username)
        if current_user == None:
            return {"message": "User does not exist."}, 400
        if new_password != repeat_new_password:
            return {"message": "Password does not match."}, 400
        if current_user.password_change_request(conn, old_password, new_password):
            return {"message": "Password has been updated."}, 200
        return {"message": "Original Password is not correct."}, 400

@api.route('/user/change_email')
class ChangeEmail(Resource):
    @api.response(200, 'Update Email Success')
    @api.response(400, 'Password Update Error')
    @api.doc(description="Change existing email of user")
    @api.expect(email_change_model, validate=True)
    @requires_auth
    def post(self):
        token = request.headers.get('AUTH-TOKEN')
        user = jwt.decode(token, SECRET_KEY, algorithm='HS256')
        email_info = request.json
        new_email = email_info['new_email']
        regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
        if not re.search(regex, new_email):
            return {"message": "Invalid Email Address."}, 400
        username = user['username']
        current_user = User.get_user_object(conn, username)
        if current_user == None:
            return {"message": "User does not exist."}, 400
        current_user.email_change(conn, new_email)
        return {"message": "Email has been updated."}, 200

@api.route('/user/')
class Profile(Resource):
    @api.response(200, 'Success')
    @api.response(401, 'Auth Failed')
    @api.response(404, 'User not found')
    @api.doc(description="Get current logged-in user profile")
    @requires_auth
    def get(self):
        token = request.headers.get('AUTH-TOKEN')
        user = jwt.decode(token, SECRET_KEY, algorithm='HS256')
        result = User.get_profile(conn, user['username'])
        if result == {}:
            api.abort(404, 'Username {} not found'.format(user['username']))
        return dict(result)

@api.route('/property/')
class Property(Resource):
    @api.response(200, 'Property Created Successfully')
    @api.response(400, 'Validation Error')
    @api.response(401, 'Auth Failed')
    @api.doc(description="Add a new property based on different aspects")
    @api.expect(property_model, validate=True)
    @requires_auth
    def post(self):
        token = request.headers.get('AUTH-TOKEN')
        user = jwt.decode(token, SECRET_KEY, algorithm='HS256')
        property = request.json
        if property['host_neighbourhood'] not in neighbourhood.index:
            return {"message": "Invalid host neighbourhood"}, 400
        if property['city'] not in neighbourhood.index:
            return {"message": "Invalid city"}, 400
        if property['property_type'] not in property_type_list[1:]:
            return {"message": "Invalid property type"}, 400
        if property['room_type'] not in room_type_list[1:]:
            return {"message": "Invalid room type"}, 400

        to_add = {
            'name': property['name'],
            'host_id': user['username'],
            'host_name': user['username'],
            'host_neighbourhood': property['host_neighbourhood'],
            'city': property['city'],
            'property_type': property['property_type'],
            'room_type': property['room_type'],
            'accommodates': property['accommodates'],
            'bathrooms': property['bathrooms'],
            'bedrooms': property['bedrooms'],
            'beds': property['beds'],
            'amenities': property['amenities'],
            'price': property['price'],
            'security_deposit': round(property['security_deposit'], 2),
            'cleaning_fee': round(property['cleaning_fee'], 2),
            'guests_included': property['guests_included'],
            'host_response_time': 0,
            'availability_60': 60,
            'availability_365': 365,
            'review_scores_rating': 80,
            'review_scores_accuracy': 3,
            'review_scores_cleanliness': 3,
            'review_scores_checkin': 3,
            'review_scores_communication': 3,
            'review_scores_location': 3,
            'review_scores_value': 3,
            'latitude': 0,
            'longitude': 0,
            'host_response_rate': 3
        }
        new_id = properties.last_valid_index() + 1
        for key in to_add.keys():
            properties.loc[new_id, key] = to_add[key]
        return {"message": "Property {} has been successfully updated".format(new_id)}, 200


@api.route('/property/<int:id>')
@api.param('id', 'The Property identifier')
class PropertyWithID(Resource):
    @api.response(200, 'Successful')
    @api.response(404, 'Property was not found')
    @api.doc(description="Get properties by ID")
    def get(self, id):
        count_api('/Property', conn)
        if id not in properties.index:
            api.abort(404, "Property {} does not exist".format(id))
        json_str = properties[properties.index == id].to_json(orient='index')
        ds = json.loads(json_str)
        return ds

    @api.response(200, 'Successful')
    @api.response(401, 'Auth Failed')
    @api.response(404, 'Property was not found')
    @api.doc(description="Delete properties by ID")
    @requires_auth
    def delete(self, id):
        if id not in properties.index:
            api.abort(404, "Property {} does not exist".format(id))
        properties.drop(id, inplace=True)
        return {"message": "Property {} is removed.".format(id)}, 200

@api.route('/property/<int:id>/price_estimate')
@api.param('id', 'The Property identifier')
class estimateReturnWithID(Resource):
    @api.response(200, 'Successful')
    @api.response(404, 'Property was not found')
    @api.doc(description='Get estimated price for property by estimating similar properties in the neighbourhood')
    def get(self, id):
        count_api('/Property/return', conn)
        if id not in properties.index:
            api.abort(404, "Property {} does not exist".format(id))
        city = properties.loc[id, 'city']
        property_type = properties.loc[id, 'property_type']
        room_type = properties.loc[id, 'room_type']
        accommodates = properties.loc[id, 'accommodates']
        similar_df = properties[(properties.city == city) | (properties.property_type == property_type) | (properties.room_type == room_type) | (properties.accommodates == accommodates)]
        estimated = similar_df['price'].mean().round(2)
        return {"return": estimated}, 200

@api.route('/property_list/')
class PropertyList(Resource):
    @api.response(200, 'Success')
    @api.response(400, 'Validation Error')
    @api.doc(description="Get a property list filtered by many different aspects")
    @api.expect(search_condition_parser, validate=True)
    @requires_auth
    def get(self):
        # get user from header
        token = request.headers.get('AUTH-TOKEN')
        user = jwt.decode(token, SECRET_KEY, algorithm='HS256')

        args = search_condition_parser.parse_args()
        min_price = args.get('min_price')
        max_price = args.get('max_price')
        suburb = args.get('suburb')
        property_type = args.get('property_type')
        room_type = args.get('room_type')
        accommodates = args.get('accommodates')
        cleanliness_rating_weight = args.get('cleanliness rating weight')
        location_rating_weight = args.get('location rating weight')
        communication_rating_weight = args.get('communication rating weight')
        order_by = args.get('order_by')
        sorting = args.get('sorting')
        page = args.get('page')

        # filters
        property_results = properties
        if suburb != 'All':
            property_results = property_results[property_results.city == suburb]
        if property_type != 'All':
            property_results = property_results[property_results.property_type == property_type]
        if room_type != 'All':
            property_results = property_results[property_results.room_type == room_type]
        if int(accommodates) != 0:
            property_results = property_results[property_results.accommodates >= accommodates]
        # price_filter
        if min_price > max_price:
            return {'message': "Invalid price range"}, 400
        elif min_price == 0 and max_price == 0:
            pass
        else:
            property_results = property_results[property_results.price <= int(max_price)]
            property_results = property_results[property_results.price >= int(min_price)]

        # sorting
        ascending = (sorting == 'ascending')
        if order_by == 'price':
            property_results.sort_values(by=order_by, inplace=True, ascending=ascending)
        else:
            property_results.sort_values(by='price', inplace=True, ascending=True)
            if order_by == 'total_rating':
                pass
            elif order_by == 'customized_rating':
                cleanliness_rating_weight, location_rating_weight, communication_rating_weight = User.get_prefs(conn, user['username'])
            else:
                return {'message': "Invalid order_by type"}, 400
            # total_rating =
            # rating[0-100] + weight1 * cleanliness[0-10] + weight2 * location[0-10] + weight3 * communication[0-10]
            property_results['total_rating'] = property_results['review_scores_rating'] + \
                                               cleanliness_rating_weight * property_results[
                                                   'review_scores_cleanliness'] + \
                                               location_rating_weight * property_results['review_scores_location'] + \
                                               communication_rating_weight * property_results[
                                                   'review_scores_communication']
            property_results.sort_values(by='total_rating', inplace=True, ascending=ascending)

        if property_results.shape[0] == 0:
            return {'message': "No search result"}, 404

        # get at most 10 results by page
        if property_results.shape[0] < 10 * (page - 1):
            return {'message': "Invalid page {} request".format(page)}, 404
        total_pages = round(property_results.shape[0]/10+0.4, 0)
        page_end = min(property_results.shape[0] + 1, 10 * page)
        property_results = property_results[10 * (page - 1):page_end]

        # generate json file
        json_str = property_results.head(10).to_json(orient='index')
        ds = json.loads(json_str)
        ret = []
        for idx in ds:
            property = ds[idx]
            ret.append(property)
        return {"list":ret, "current":page, "total":total_pages}, 200


@api.route('/property/<int:id>/date_price')
@api.param('id', 'The Property identifier')
class PriceList(Resource):
    @api.response(200, 'Successful')
    @api.response(404, 'Property was not found')
    @api.response(401, 'Auth Failed')
    @api.doc(description="Get properties datetime and price by ID")
    @requires_auth
    def get(self, id):
        date_price_list = []
        #print(calendar)
        #print(id)
        #print("before query = " + str(calendar.shape[0]))
        calendar_results = calendar[calendar.listing_id == id]
        #print("length = " + str(calendar_results.shape[0]))
        for row_num in range(0, calendar_results.shape[0]):
            date_price_list.append((calendar_results.iloc[row_num]['date'], calendar_results.iloc[row_num]['price']))
        return dict(date_price_list), 200

@api.route('/property/<int:id>/prediction')
@api.param('id', 'The property identifier')
#@api.param('date', 'The prediction date, Year-Month-Date, eg: 2019-12-12')
class Prediction(Resource):
    @api.response(200, 'Successful')
    @api.response(401, 'Auth Failed')
    @api.response(400, 'Bad Request')
    @api.doc(description="Predict price of property in specific date")
    @api.expect(prediction_parser, validate=True)
    @requires_auth
    def get(self, id):
        args = prediction_parser.parse_args()
        property_id = id
        date = args.get('date')
        predicted_price = predict(property_id, date)
        if predicted_price is None:
            return {"The historical data is not enough for prediction"}, 401

        else:
            return {'predicted_price': predicted_price}, 200


def read_csv(csv_file):
    return pd.read_csv(csv_file, dtype='str')


def count_api(api, conn):
    query = 'INSERT INTO api_calls (api, calls) VALUES (\'' + api + '\', 1) ON CONFLICT (api) DO UPDATE SET calls = api_calls.calls + 1;'
    conn.execute(query)


def count_api(api, conn):
    query = 'INSERT INTO api_calls (api, calls) VALUES (\'' + api + '\', 1) ON CONFLICT (api) DO UPDATE SET calls = api_calls.calls + 1;'
    conn.execute(query)


if __name__ == '__main__':
    engine = create_engine('postgresql://cs9321:comp9321@ali.x-zhou.com:5432/comp9321')
    conn = engine.connect()

    # initialize listings_df => properties
    properties = read_csv('listing.csv')
    properties['id'] = pd.to_numeric(properties['id'])
    properties['price'] = pd.to_numeric(properties['price'])
    properties['review_scores_rating'] = pd.to_numeric(properties['review_scores_rating'])
    properties['review_scores_cleanliness'] = pd.to_numeric(properties['review_scores_cleanliness'])
    properties['review_scores_communication'] = pd.to_numeric(properties['review_scores_communication'])
    properties['review_scores_location'] = pd.to_numeric(properties['review_scores_location'])
    properties['accommodates'] = pd.to_numeric(properties['accommodates'])
    properties['property_id'] = properties['id']

    properties.set_index('id', inplace=True)

    # initialize neighbourhood_df => neighbourhood
    # usage: using neighbourhood['name'] to find neighbourhood, if is does not exist, raise keyError
    neighbourhood = read_csv('neighbour.csv')
    neighbourhood.set_index('neighbourhood', inplace=True)

    # initialize calendar_df => calendar
    calendar = read_csv('calendar.csv')
    calendar['listing_id'] = pd.to_numeric(calendar['listing_id'])

    app.run(debug=True)
