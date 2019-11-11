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

def read_csv(csv_file):
	return pd.read_csv(csv_file)

def write_csv(df, target):
	df.to_csv(target, sep=',', encoding='utf-8')

if __name__ == '__main__':
	print("====== Starting Preprocess ======")

	print("====== Preprocess Finished ======")
