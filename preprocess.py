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
pandas 0.25.0
sqlalchemy 1.3.10
'''

import pandas as pd

def read_csv(csv_file):
	return pd.read_csv(csv_file)

def write_csv(df, target):
	df.to_csv(target, sep=',', encoding='utf-8')

if __name__ == '__main__':
	print("====== Starting Preprocess ======")

	# related files
	data_dir = "syd_airbnb_open_data/"
	calendar_file = data_dir + "calendar_dec18.csv"
	listings_file = data_dir + "listings_dec18.csv"
	neighbourhoods_file = data_dir + "neighbourhoods_dec18.csv"
	# read into dataFrame
	calendar_df = read_csv(calendar_file)
	listings_df = read_csv(listings_file)
	neighbourhoods_df = read_csv(neighbourhoods_file)

	print(calendar_df)
	print(listings_df)
	print(neighbourhoods_df)

	print("====== Preprocess Finished ======")
