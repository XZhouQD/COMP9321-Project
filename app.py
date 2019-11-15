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
from flask import Flask, request
from flask_restplus import Resource, Api, fields
from sqlalchemy import create_engine

app = Flask(__name__)
api = Api(app)

@api.route('/listing/<int:id>')
class Listing(Resource):
	def get(self, id):
		countApi('/listing', conn)
		if id not in listings.index:
			api.abort(404, "Listing {} does not exist".format(id))
		return dict(listings.loc[id])

def read_csv(csv_file):
	return pd.read_csv(csv_file, dtype='str')

def countApi(api, conn):
        query = 'INSERT INTO api_calls (api, calls) VALUES (\'' + api + '\', 1) ON CONFLICT (api) DO UPDATE SET calls = api_calls.calls + 1;'
        conn.execute(query)

if __name__ == '__main__':
	engine = create_engine('postgresql://cs9321:comp9321@ali.x-zhou.com:5432/comp9321')
	conn = engine.connect()
	calendar = read_csv('syd_airbnb_open_data/calendar_dec18.csv')
	listings = read_csv('listing.csv')
	listings['id'] = pd.to_numeric(listings['id'])
	listings.set_index('id', inplace=True)

	neighbourhood = read_csv('neighbour.csv')

	app.run(debug=True)
