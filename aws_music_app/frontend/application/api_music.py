# ./frontend/application/api_music.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app
# from flask_login import login_required, current_music, logout_music
# from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from .model.musics import Music  
from .model.sessions import Session 
import requests



# Blueprint Configuration
music_api = Blueprint("music_api", __name__)
base_url = current_app.config['BASE_BACKEND_URL']



@music_api.route('/unsubscribe_music/<string:music_id>', methods=['POST'])
@login_required
def unsubscribe_music(music_id):
    user_email = current_user.email
    base_url = current_app.config['BASE_BACKEND_URL']
    api_url = f"{base_url}/favorites/remove/"
    params = {
        'user_email': user_email,
        'music_id': music_id
    }
    response = requests.delete(api_url, params=params)
    if response.status_code == 200:
        flash('Music removed from favorites successfully')
    else:
        flash('Failed to remove music from favorites', 'error')
    return redirect(request.referrer)




@music_api.route('/admin/musics/all/<int:page_num>', methods=['GET'])
@login_required
def get_musics_admin(page_num):
    base_url = current_app.config['BASE_BACKEND_URL']
    api_url = f"{base_url}/musics/all/"
    headers = {'Content-Type': 'application/json'}
    per_page = request.args.get('per_page', 10, type=int)

    response = requests.get(api_url, headers=headers)
    if response.status_code == 200:
        all_musics = response.json()
        total = len(all_musics)

        # Calculate the pagination details
        start = (page_num - 1) * per_page
        end = start + per_page
        musics = all_musics[start:end]  # Slice the list to get only the musics for this page

    else:
        flash('Failed to fetch musics')
        musics = []
        total = 0

    # Render template with pagination
    return render_template('screen/music_handler.html', musics=musics, page=page_num, per_page=per_page, total=total)



@music_api.route('/add_to_favorites/<string:music_id>', methods=['POST'])
@login_required
def add_to_favorites(music_id):
    user_email = current_user.email
    base_url = current_app.config['BASE_BACKEND_URL']
    api_url = f"{base_url}/favorites/add/"
    params = {
        'user_email': user_email,
        'music_id': music_id
    }
    response = requests.post(api_url, params=params)
    
    if response.status_code == 200:
        # Check for specific messages in the response JSON
        message = response.json().get('message')
        if message == "This music has already been added to your favorites.":
            flash('This music is already in your favorites.', 'warning')
        else:
            flash('Music added to favorites successfully')
    else:
        flash('Failed to add music to favorites', 'error')
    
    return redirect(request.referrer)



@music_api.route('/explore-music-table', methods=['GET'])
@login_required
def explore_music():
    ''' Search unsubscribed music with pagination '''
    api_url = f"{base_url}/musics/unsubscribed/"
    headers = {'Content-Type': 'application/json'}

    # Get search and pagination parameters from the form
    search_music_title = request.args.get('search_music_title', '')
    search_music_artist = request.args.get('search_music_artist', '')
    search_music_year = request.args.get('search_music_year', '')
    page_num = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    params = {
        'search_music_title': search_music_title,
        'search_music_artist': search_music_artist,
        'search_music_year': search_music_year,
        'page': page_num,
        'per_page': per_page
    }

    response = requests.get(api_url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        musics = data['musics']
        total = data['total']
        print(musics)
    else:
        flash('Failed to fetch music')
        musics = []
        total = 0

    return render_template('screen/unsubscribed_music_handler.html', musics=musics, page=page_num, per_page=per_page, total=total)



@music_api.route('/search_subscribed_music', methods=['GET'])
@login_required
def search_subscribed_music():
    ''' Search subscribed music with filters '''
    api_url = f"{base_url}/favorites/search/"
    headers = {'Content-Type': 'application/json'}

    # Get search parameters from the form
    search_music_title = request.args.get('search_music_title', '')
    search_music_artist = request.args.get('search_music_artist', '')
    search_music_year = request.args.get('search_music_year', '')

    params = {
        'user_email': current_user.email,
        'search_music_title': search_music_title,
        'search_music_artist': search_music_artist,
        'search_music_year': search_music_year
    }

    response = requests.get(api_url, headers=headers, params=params)
    if response.status_code == 200:
        data = response.json()
        musics = data.get('musics', [])
        total = data.get('total', 0)
        print(musics)
        if total == 0:
            flash('Music not found', 'warning')  # Flash a message when no music is found

    else:
        flash('Music not found', 'error')
        musics = []
        total = 0

    return render_template('screen/subscribed_music_handler.html', musics=musics, total=total, per_page=10, page = 1)

