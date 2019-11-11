#!/usr/bin/python3

from sqlalchemy import create_engine
import pandas as pd
import numpy as np

engine = create_engine('postgresql://cs9321:comp9321@ali.x-zhou.com:5432/comp9321')
data = pd.DataFrame(np.arange(20).reshape(4, 5),index=['one','two','three','four'],columns=['a','b','c','d','e'])
try:
	data.to_sql('test_table',engine,index=False,if_exists='replace')
except Exception as e:
	print(e)
