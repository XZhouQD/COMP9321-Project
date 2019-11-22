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
    def __init__(self, username, email, password_plain='', password_encrypted='', role='default', uuid=''):
        self.username = username
        self.email = email
        if password_encrypted == "":
            self.password_encrypted = sha256(password_plain)
        else:
            self.password_encrypted = password_encrypted
        self.role = role
        if not uuid == '':
            self.uuid = uuid
        else:
            self.uuid = uuid1()

    @staticmethod
    def login(conn, username, password_plain):
        query = 'select * from users where username = \'' + username + '\';'
        result = conn.execute(query)
        if result.rowcount == 0:
            return None
        row = result.fetchone()
        temp_user = User(row['username'], row['email'], password_encrypted=row['password'], role=row['role'],
                         uuid=row['uuid'])
        if temp_user.check_password(password_plain):
            return {'username': username, 'role': row['role']}
        else:
            return None
            
    @staticmethod
    def get_user_object(conn, username):
        query = 'select * from users where username = \'' + username + '\';'
        result = conn.execute(query)
        if result.rowcount == 0:
            return None
        row = result.fetchone()
        temp_user = User(row['username'], row['email'], password_encrypted=row['password'], role=row['role'],
                         uuid=row['uuid'])
        return temp_user

    @staticmethod
    def is_username_exists(conn, username):
        query = 'select * from users where username = \'' + username + '\';'
        result = conn.execute(query)
        if result.rowcount == 0:
            return False
        return True
        
    @staticmethod
    def set_prefs(conn, username, cleanliness=1, location=1, communication=1):
        query = 'INSERT INTO user_prefs(username, cleanliness_weight, location_weight, communication_weight) VALUES (\'' + username + '\', '+str(cleanliness) + ', ' + str(location) + ', ' + str(communication) + ') ON CONFLICT (username) DO UPDATE SET cleanliness_weight = ' + str(cleanliness) + ', location_weight = ' + str(location) + ', communication_weight = ' + str(communication) + ';'
        conn.execute(query)
        
    @staticmethod
    def get_prefs(conn, username):
        query = 'select * from user_prefs where username = \'' + username + '\';'
        result = conn.execute(query)
        if result.rowcount == 0:
            return 1, 1, 1
        row = result.fetchone()
        return row['cleanliness_weight'], row['location_weight'], row['communication_weight']

    @staticmethod
    def get_profile(conn, username):
        query = 'select username, email, role from users where username = \'' + username + '\';'
        result = conn.execute(query)
        if result.rowcount == 0:
            return {}
        row = result.fetchone()
        return row
        
    def password_change_request(self, conn, origin_password, new_password):
        if self.password_encrypted == sha256(origin_password):
            self.password_encrypted = sha256(new_password)
            self.commit(conn)
            return True
        return False

    def email_change(self, conn, new_email):
        self.email = new_email
        self.commit(conn)

    def get_uuid(self):
        return self.uuid

    def get_email(self):
        return self.email

    def check_password(self, password_input):
        return sha256(password_input) == self.password_encrypted

    def update_role(self, role='default'):
        self.role = role

    def commit(self, conn):
        query = 'INSERT INTO users (uuid, username, email, password, role) VALUES (\'' + str(
            self.uuid) + '\', \'' + self.username + '\', \'' + self.email + '\', \'' + self.password_encrypted + '\', \'' + self.role + '\') ON CONFLICT (uuid) DO UPDATE SET password = \'' + self.password_encrypted + '\', email = \'' + self.email + '\', role = \'' + self.role + '\';'
        conn.execute(query)

    def __str__(self):
        return str(self.uuid) + ':' + self.username + ':' + self.role + ':' + self.email + ':' + self.password_encrypted
