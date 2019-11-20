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


credential_parser = reqparse.RequestParser()
credential_parser.add_argument('username', type=str)
credential_parser.add_argument('password', type=str)

# id, => list.id[-1]+1
# name, => field.String
# host_id => autoGetFromUser
# host_name, => username
# host_neighbourhood, => field.String
# city, => field.String
# property_type, =>field.Enum
# room_type, =>field.Enum
# accommodates, =>field.integer
# bathrooms, =>field.integer
# bedrooms, =>field.integer
# beds, =>field.integer
# amenities, => Set of String
# price, =>field.double
# security_deposit, =>field.double
# cleaning_fee, =>field.double
# guests_included, =>field.integer
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
    'price': fields.Arbitrary,
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


@api.route('/properties/<int:id>')
@api.param('id', 'The Property identifier')
class Properties(Resource):
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


@api.route('/property/')
class PropertyList(Resource):
    # 'name': fields.String,
    # 'host_neighbourhood': fields.String,
    # 'city': fields.String,
    # 'property_type': fields.String,
    # 'room_type': fields.String,
    # 'bathrooms': fields.Integer,
    # 'bedrooms': fields.Integer,
    # 'beds': fields.Integer,
    # 'amenities': fields.String,
    # 'price': fields.Arbitrary,
    # 'security_deposit': fields.Float,
    # 'cleaning_fee': fields.Float,
    # 'guests_included': fields.Integer
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
        if property['property_type'] not in ['aparthotel', 'apartment', 'barn', 'bed and breakfast',
                                             'boat', 'boutique hotel', 'bungalow', 'cabin', 'camper/rv',
                                             'campsite', 'casa particular(cuba)', 'castle', 'cave', 'chalet',
                                             'condominium', 'cottage', 'dome house', 'earth house', 'farm stay',
                                             'guest suite', 'guesthouse', 'heritage hotel(India)', 'hostel',
                                             'hotel', 'house', 'house', 'hut', 'island', 'loft', 'nature  lodge',
                                             'other', 'resort', 'serviced apartment', 'tent', 'tiny house', 'tipi',
                                             'townhouse', 'train', 'treehouse', 'villa', 'yurt']:
            return {"message": "Invalid property type"}, 400
        if property['room_type'] not in ['private room', 'entire room/apt', 'shared room']:
            return {"message": "Invalid room type"}, 400

        print(properties.keys())

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
            'review_scores_rating': 0,
            'review_scores_accuracy': 0,
            'review_scores_cleanliness': 0,
            'review_scores_checkin': 0,
            'review_scores_communication': 0,
            'review_scores_location': 0,
            'review_scores_value': 0,
            'latitude': 0,
            'longitude': 0,
            'host_response_rate': 0
        }
        new_id = properties.last_valid_index() + 1
        for key in to_add.keys():
            properties.loc[new_id, key] = to_add[key]
        return {"message": "Property {} has been successfully updated".format(new_id)}, 200


@api.route('/calendar/<int:id>')
@api.param('id', 'The Property identifier')
class PriceList(Resource):
    @api.response(200, 'Successful')
    @api.response(404, 'Property was not found')
    @api.doc(description="Get properties datetime and price by ID")
    def get(self, id):
        date_price_list = []
        calendar_results = calendar[calendar.listing_id == '14250']
        for row_num in range(0, calendar_results.shape[0]):
            date_price_list.append((calendar_results.iloc[row_num]['date'], calendar_results.iloc[row_num]['price']))
        return dict(date_price_list)




def read_csv(csv_file):
    return pd.read_csv(csv_file, dtype='str')


def count_api(api, conn):
    query = 'INSERT INTO api_calls (api, calls) VALUES (\'' + api + '\', 1) ON CONFLICT (api) DO UPDATE SET calls = api_calls.calls + 1;'
    conn.execute(query)


if __name__ == '__main__':
    engine = create_engine('postgresql://cs9321:comp9321@ali.x-zhou.com:5432/comp9321')
    conn = engine.connect()

    # initialize listings_df => properties
    properties = read_csv('listing.csv')
    properties['id'] = pd.to_numeric(properties['id'])
    properties.set_index('id', inplace=True)

    # initialize neighbourhood_df => neighbourhood
    # usage: using neighbourhood['name'] to find neighbourhood, if is does not exist, raise keyError
    neighbourhood = read_csv('neighbour.csv')
    neighbourhood.set_index('neighbourhood', inplace=True)

    # initialize calendar_df => calendar
    calendar = read_csv('calendar.csv')

    app.run(debug=True)
