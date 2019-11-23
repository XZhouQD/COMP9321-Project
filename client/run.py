import os, glob, re, collections, subprocess, random, csv, json, requests
from flask import Flask, render_template, session, request, redirect, url_for, Response


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
token = None
server_url = 'http://127.0.0.1:5000/'


@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    global token
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        params = {'username': username, 'password': password}
        if username == '' or password == '':
            return render_template('login.html', notFilledInError=True)
        api_url = server_url + 'token'
        try:
            response = requests.get(api_url, params=params)
        except requests.exceptions.ConnectionError:
            return Response("<script> window.alert('No server connection') </script>")
        if response.ok:
            token = response.json()['token']
            # redirect to the next page
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', invalidPassWordError=True)
    else:
        return render_template('login.html', invalidPassWordError=False)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        email = request.form['email']
        if username == '' or password == '' or confirm_password == '' or email == '':
            return render_template('login.html', notFilledInError=True)
        api_url = server_url + 'register'
        post_json = {'username': username, 'email': email, 'password': password, 'repeat_password': confirm_password}
        try:
            resp = requests.post(api_url, json=post_json)
        except requests.exceptions.ConnectionError:
            return Response("<script> window.alert('No connection between the server!') </script>")
        if resp.status_code == 200:
            return render_template('login.html', registerSuccessfully=True)
        elif resp.status_code == 400:
            return render_template ('register.html', errorMsg=resp.json()['message'])
        else:
            return redirect(url_for('register'))
    else:
        return render_template ('register.html')


@app.route('/dashboard', methods=['GET'])
def dashboard():
    # get user info
    api_url = server_url + 'user'
    # put header
    header = {'AUTH-TOKEN': token}
    resp = requests.get(api_url, headers=header)
    username = resp.json()['username']
    email = resp.json()['email']
    role = resp.json()['role']
    cleanliness_weight = resp.json()['cleanliness_weight']
    location_weight = resp.json()['location_weight']
    communication_weight = resp.json()['communication_weight']
    return render_template('dashboard.html',
                           username=username,
                           email=email,
                           role=role,
                           cleanliness_weight=cleanliness_weight,
                           location_weight=location_weight,
                           communication_weight=communication_weight)


@app.route('/logout', methods=['GET'])
def logout():
    global token
    if token is not None:
        headers = {'AUTH-TOKEN': token}
        url = 'http://0.0.0.0:12345/signout/' + token
        try:
            resp = requests.delete(url, headers=headers)
        except requests.exceptions.ConnectionError:
            return Response("<script> window.alert('No connection between the server!') </script>")

    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug =True, port=12000)
