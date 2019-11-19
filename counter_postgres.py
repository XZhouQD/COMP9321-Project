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

from sqlalchemy import create_engine
import pandas as pd


def countApi(api, conn):
	query = 'INSERT INTO api_calls (api, calls) VALUES (\'' + api + '\', 1) ON CONFLICT (api) DO UPDATE SET calls = api_calls.calls + 1;'
	conn.execute(query)
	#df = pd.read_sql_table('api_calls', engine, index_col='api')
	#if api not in df.index:
	#	df.loc[api] = 1;
	#else:
	#	df.loc[api] += 1
	#df.to_sql('api_calls', engine, if_exists='replace')

if __name__ == '__main__' :
	engine = create_engine('postgresql://cs9321:comp9321@ali.x-zhou.com:5432/comp9321')
	conn = engine.connect()
	countApi('/placeholder', conn)
	countApi('/placeholder2', conn)
	countApi('/placeholder3', conn)
	conn.close()
