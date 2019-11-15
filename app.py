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

app = Flask(__name__)
api = Api(app)

@api.route('/listing/<int:id>')
class Listing(Resource):
	def get(self, id):
		if id not in listings.index:
			api.abort(404, "Listing {} does not exist".format(id))
		#json = listings.loc[id].to_json(orient='records')
		return dict(listings.loc[id])

def read_csv(csv_file):
	return pd.read_csv(csv_file, dtype='str')

if __name__ == '__main__':
	calendar = read_csv('syd_airbnb_open_data/calendar_dec18.csv')
	listings = read_csv('listing.csv')
	listings['id'] = pd.to_numeric(listings['id'])
	listings.set_index('id', inplace=True)

#	print(listings.dtypes)
#	for column in listings.columns :
#		if listings[column].dtype == 'int64':
#			listings[column] = listings[column].astype('int32')
#	print(listings.dtypes)
	neighbourhood = read_csv('neighbour.csv')

	app.run(debug=True)
