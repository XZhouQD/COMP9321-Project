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
import hashlib

def sha256(hash_string):
	m = hashlib.sha256()
	m.update(hash_string.encode())
	return m.hexdigest()

