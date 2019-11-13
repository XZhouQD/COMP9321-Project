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
from utils import sha256
from uuid import uuid1

class User():
	def __init__(self, username, email, password_plain="", password_encrypted=""):
		self.username = username
		self.email = email
		if password_encrypted == "":
			self.password_encrypted = sha256(password_plain)
		else:
			self.password_encrypted = password_encrypted;
		self.uuid = uuid1()

	def password_change_request(self, origin_password, new_password, forget=False):
		if forget:
			self.password_encrypted = sha256(new_password)
			return True
		else:
			if self.password_encrypted == sha256(new_password):
				self.password_encrypted = sha256(new_password)
				return True
		return False

	def email_change(self, new_email):
		self.email = new_email

	def getUUID(self):
		return self.uuid

	def getEmail(self):
		return self.email

	def checkPassword(self, password_input):
		return sha256(password_input) == self.password_encrypted

	def __str__(self):
		return str(self.uuid) + ':' + self.username + ':' + self.email + ':' + self.password_encrypted
