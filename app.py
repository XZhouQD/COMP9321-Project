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

        

# =================== login ===================
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


@api.route('/Properties/<int:id>')
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

def read_csv(csv_file):
	return pd.read_csv(csv_file, dtype='str')

def count_api(api, conn):
	query = 'INSERT INTO api_calls (api, calls) VALUES (\'' + api + '\', 1) ON CONFLICT (api) DO UPDATE SET calls = api_calls.calls + 1;'
	conn.execute(query)

# =================== register ===================

@api.route('/register')
class Register(Resource):
	@api.response(200, 'Successful')
	@api.response(404, 'Registration Failed')
	@api.doc(description="Create a new user")
	@api.expect(credential_parser, validate=True)
	def post(self):
		args = credential_parser.parse_args()
		username = args.get('username')
		email = args.get('email')
		password = args.get('password')
		confirm_password = args.get('confirm password')
		user = User.login(conn, username, password)
		if user is not None:
			return {"message": "username is existed."},404
		if password != confirm_password:
			return {"message": "passwords are not consistent."}, 404
		#insert new user info
		User(username, email, password_plain=password, password_encrypted='', role='default', uuid='').commit(conn)
		return {"message": "welcome to our family, {}".format(username)}, 200


if __name__ == '__main__':
	engine = create_engine('postgresql://cs9321:comp9321@ali.x-zhou.com:5432/comp9321')
	conn = engine.connect()
	properties = read_csv('listing.csv')
	properties['id'] = pd.to_numeric(properties['id'])
	properties.set_index('id', inplace=True)

	neighbourhood = read_csv('neighbour.csv')

	app.run(debug=True)
