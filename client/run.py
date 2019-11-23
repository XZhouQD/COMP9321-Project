import os, glob, re, collections, subprocess, random, csv, json, requests
from flask import Flask, render_template, session, request, redirect, url_for, Response


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'
token = None
server_url = 'http://127.0.0.1:5000/'

is_login = False


@app.route('/', methods=['GET', 'POST'])
def home():
    return render_template('index.html', is_login=is_login)


@app.route('/login', methods=['GET', 'POST'])
def login():
    global token
    global is_login
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        params = {'username': username, 'password': password}
        if username == '' or password == '':
            return render_template('login.html', notFilledInError=True, is_login=is_login)
        api_url = server_url + 'token'
        try:
            response = requests.get(api_url, params=params)
        except requests.exceptions.ConnectionError:
            return Response("<script> window.alert('No server connection') </script>")
        if response.ok:
            token = response.json()['token']
            is_login = True
            print(is_login)
            # redirect to the next page
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', invalidPassWordError=True, is_login=is_login)
    else:
        return render_template('login.html', invalidPassWordError=False, is_login=is_login)


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
            return render_template('login.html', registerSuccessfully=True, is_login=is_login)
        elif resp.status_code == 400:
            return render_template ('register.html', errorMsg=resp.json()['message'], is_login=is_login)
        else:
            return render_template ('register.html', is_login=is_login)
    else:
        return render_template ('register.html', is_login=is_login)


@app.route('/dashboard', methods=['GET'])
def dashboard():
    if is_login:
        # get user info
        api_url = server_url + 'user'
        # put header
        header = {'AUTH-TOKEN': token}
        resp = requests.get(api_url, headers=header)
        if resp.ok:
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
        else:
            redirect(url_for('page_not_found'))
    else:
        return redirect(url_for('page_not_found'))


@app.route('/404', methods=['GET'])
def page_not_found():
    return render_template('404.html')


@app.route('/property/', methods=['GET', 'POST'])
def get_property():
    if request.method == 'POST':
        property_id = request.form['property_id']
        return redirect(url_for('get_property_details', property_id=property_id))
    else:
        return render_template('property_selection.html')


@app.route('/property/<string:property_id>', methods=['GET'])
def get_property_details(property_id):
    if is_login:
        api_url = server_url + 'property/' + property_id
        header = {'AUTH-TOKEN': token}
        resp = requests.get(api_url, headers=header)
        if resp.ok:
            property_details = resp.json()
            return render_template('property.html', property_details=property_details, property_id=property_id)
        else:
            return redirect(url_for('page_not_found'))
    else:
        return redirect(url_for('page_not_found'))


@app.route('/add_property/', methods=['GET', 'POST'])
def add_property():
    if is_login:
        if request.method == 'POST':
            api_url = server_url + 'property/'
            header = {'AUTH-TOKEN': token}
            params = {
                "name": request.form['name'],
                "host_neighbourhood": request.form['host_neighbourhood'],
                "city": request.form['city'],
                "property_type": request.form['property_type'],
                "room_type": request.form['room_type'],
                "accommodates": int(request.form['accommodates']),
                "bathrooms": int(request.form['bathrooms']),
                "bedrooms": int(request.form['bedrooms']),
                "beds": int(request.form['beds']),
                "amenities": "string",
                "price": float(request.form['price']),
                "security_deposit": float(request.form['security_deposit']),
                "cleaning_fee": float(request.form['cleaning_fee']),
                "guests_included": int(request.form['guests_included'])
            }
            resp = requests.post(api_url, json=params, headers=header)
            return render_template('add_property.html', message=resp.json()['message'])
        else:
            return render_template('add_property.html')
    else:
        return redirect(url_for('page_not_found'))


@app.route('/delete_property', methods=['GET', 'POST'])
def delete_property():
    if is_login:
        if request.method == 'POST':
            to_delete = request.form['to_delete']
            api_url = server_url + 'property/' + to_delete
            header = {'AUTH-TOKEN': token}
            resp = requests.delete(api_url, headers=header)
            return render_template('delete_property.html', message=resp.json()['message'])
        else:
            return render_template('delete_property.html')
    else:
        return redirect(url_for('page_not_found'))


@app.route('/property_filter', methods=['GET', 'POST'])
def property_filter():
    if is_login:
        api_url = server_url + 'property_list'
        header = {'AUTH-TOKEN': token}
        if request.method == 'POST':
            page = request.form['page']
            params = {
                'min_price': int(request.form['min_price']),
                'max_price': int(request.form['max_price']),
                'suburb': request.form['suburb'],
                'property_type': request.form['property_type'],
                'room_type': request.form['room_type'],
                'accommodates': int(request.form['accommodates']),
                'cleanliness rating weight': int(request.form['cleanliness rating weight']),
                'location rating weight': int(request.form['location rating weight']),
                'communication rating weight': int(request.form['communication rating weight']),
                'order_by': request.form['order_by'],
                'sorting': request.form['sorting'],
                'page': request.form['page']
            }
            resp = requests.get(api_url, headers=header, params=params)
            if resp.ok:
                return render_template('filter.html', property_list=resp.json()['list'], pages=resp.json()['total'], page=page)
            else:
                return render_template('filter.html', message=resp.json()['message'])
        else:
            resp = requests.get(api_url, headers=header)
            return render_template('filter.html', property_list=resp.json()['list'], pages=resp.json()['total'])
    else:
        return redirect(url_for('page_not_found'))



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
