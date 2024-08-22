# ./frontend/application/homesite.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app
# from flask_login import login_required, current_user, logout_user
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import check_password_hash
from .model.users import User  
from .model.sessions import Session 
import requests
import bcrypt


# Blueprint Configuration
site = Blueprint("site", __name__)
base_url = current_app.config['BASE_BACKEND_URL']



# Login page
@site.route('/register', methods=['GET', 'POST'])
def registerPage():
    if request.method == 'POST':
        email = request.form['email']
        user_name = request.form['user_name']
        password = request.form['password']
        
        # URL of the external API
        api_url = f"{current_app.config['BASE_BACKEND_URL']}/register/"
        headers = {'Content-Type': 'application/json'}
        payload = {'email': email, 'password': password, 'user_name' : user_name}

        # Make the POST request
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            session['logged_in'] = True
            user = User(name=user_data['user_name'], email=user_data['email'], password= password)
            # Assuming login_user is defined to handle user sessions
            session['name'] = user_data['user_name']
            session['email'] = email
            login_user(user)

            return redirect(url_for('site.homePage'))
        else:
            flash('Login failed. Please check your credentials.')
            return redirect(url_for('site.loginPage'))

    return render_template('auth/register.html')



@site.route('/home/', methods=['GET'])
@login_required
def homePage():
    ''' Show user's favorite music with pagination '''
    user_email = current_user.email
    api_url = f"{base_url}/favorites/"
    headers = {'Content-Type': 'application/json'}

    # Get pagination parameters
    page_num = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Request the user's favorite music with pagination parameters
    response = requests.get(api_url, headers=headers, params={'user_email': user_email, 'page': page_num, 'per_page': per_page})
    if response.status_code == 200:
        data = response.json()
        favorite_musics = data['favorites']
        total = data['total']
    else:
        flash('Failed to fetch favorite music')
        favorite_musics = []
        total = 0

    return render_template('screen/user_handler.html', favorite_musics=favorite_musics, page=page_num, per_page=per_page, total=total)


# Welcome page
@site.route('/')
async def index():
    """Display Index page

    Returns:
        .html -- The Index page of the web application
    """
    if current_user.is_authenticated:
        return redirect(url_for('site.homePage'))
    else:
        return render_template('auth/index.html')


# Login page
@site.route('/login', methods=['GET', 'POST'])
def loginPage():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # URL of the external API
        api_url = f"{current_app.config['BASE_BACKEND_URL']}/login/"
        headers = {'Content-Type': 'application/json'}
        payload = {'email': email, 'password': password}

        # Make the POST request
        response = requests.post(api_url, json=payload, headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            session['logged_in'] = True
            user = User(name=user_data['user_name'], email=user_data['email'], password= password)
            # Assuming login_user is defined to handle user sessions
            session['name'] = user_data['user_name']
            session['email'] = email
            login_user(user)

            return redirect(url_for('site.homePage'))
        else:
            flash('Login failed. Please check your credentials.')
            return redirect(url_for('site.loginPage'))

    return render_template('auth/login.html')
    
    
    
# Endpoint to logout
@site.route('/logout')
@login_required
async def logout():

    # Remove the user ID from the session if it is there
    # Logout user clear _id of the session
    logout_user()
    session.clear()

    return redirect(url_for('site.index'))
