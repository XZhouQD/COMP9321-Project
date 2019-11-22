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
          description="TODO: edit description")  # Documentation Description

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
        print(info)
        return jwt.encode(info, self._secret_key, algorithm='HS256')

    def validate_token(self, token):
        info = jwt.decode(token, self._secret_key, algorithm='HS256')
        # check whether the token is expire or not
        if time() - info['creation_time'] > self._expires_in:
            raise SignatureExpired("The Token has been expired; get a new token")
        return info['username']


SECRET_KEY = "A SECRET KEY; USUALLY A VERY LONG RANDOM STRING"
expires_in = 600
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

register_parser = reqparse.RequestParser()
register_parser.add_argument('username', type=str)
register_parser.add_argument('password', type=str)
register_parser.add_argument('email', type=str)

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


@api.route('/token')
class Token(Resource):
    @api.response(200, 'Successful')
    @api.doc(description="Generates a authentication token")
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
            print(jwt.decode(token, SECRET_KEY, algorithm='HS256'))
            return {'token': auth.generate_token(user).decode()}


@api.route('/register')
class Register(Resource):
    @api.response(200, 'Successful')
    @api.response(400, 'Registration Failed')
    @api.doc(description="Generates a new user")
    @api.expect(register_parser, validate=True)
    def get(self):
        args = register_parser.parse_args()
        username = args.get('username')
        password = args.get('password')
        email = args.get('email')
        # check email format
        regex = '^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$'
        if not re.search(regex, email):
            return {"message": "Invalid Email Address."}, 400
        if User.is_username_exists(conn, username):
            return {"message": "username exists."}, 400
        else:
            User(username, email, password).commit(conn)
            return {"message": "Register Successfully"}, 200


@api.route('/property/')
class Property(Resource):
    @api.response(201, 'Property Created Successfully')
    @api.response(400, 'Validation Error')
    @api.doc(description="Add a new book")
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
        property = dict(properties.loc[id])
        return property

    @api.response(200, 'Successful')
    @api.response(400, 'Validation Error')
    @api.response(404, 'Property was not found')
    @api.doc(description="Delete properties by ID")
    @requires_auth
    def delete(self, id):
        if id not in properties.index:
            api.abort(404, "Property {} does not exist".format(id))
        properties.drop(id, inplace=True)
        return {"message": "Property {} is removed.".format(id)}, 200


@api.route('/property_list/')
class PropertyList(Resource):
    @api.response(201, 'Property Created Successfully')
    @api.response(400, 'Validation Error')
    @api.doc(description="Get a property list by many different")
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
        page_end = min(property_results.shape[0] + 1, 10 * page)
        property_results = property_results[10 * (page - 1):page_end]

        # generate json file
        json_str = property_results.head(10).to_json(orient='index')
        ds = json.loads(json_str)
        ret = []
        for idx in ds:
            property = ds[idx]
            ret.append(property)
        return ret


@api.route('/date_price/<int:id>')
@api.param('id', 'The Property identifier')
class PriceList(Resource):
    @api.response(200, 'Successful')
    @api.response(404, 'Property was not found')
    @api.response(400, 'Validation Error')
    @api.doc(description="Get properties datetime and price by ID")
    @requires_auth
    def get(self, id):
        date_price_list = []
        calendar_results = calendar[calendar.listing_id == id]
        for row_num in range(0, calendar_results.shape[0]):
            date_price_list.append((calendar_results.iloc[row_num]['date'], calendar_results.iloc[row_num]['price']))
        return dict(date_price_list)


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

    properties.set_index('id', inplace=True)

    # initialize neighbourhood_df => neighbourhood
    # usage: using neighbourhood['name'] to find neighbourhood, if is does not exist, raise keyError
    neighbourhood = read_csv('neighbour.csv')
    neighbourhood.set_index('neighbourhood', inplace=True)

    # initialize calendar_df => calendar
    calendar = read_csv('calendar.csv')

    app.run(debug=True)
