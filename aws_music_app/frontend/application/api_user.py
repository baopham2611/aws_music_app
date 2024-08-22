# ./frontend/application/api_user.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, current_app
# from flask_login import login_required, current_user, logout_user
# from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.security import check_password_hash
from .model.users import User  
from .model.sessions import Session 
import requests


# Blueprint Configuration
user_api = Blueprint("user_api", __name__)
base_url = current_app.config['BASE_BACKEND_URL']



@user_api.route('/search_my_music/', methods=['GET'])
@login_required
def search_user():
    search_params = {
        'name': request.args.get('search_user_name', '').strip(),
        'email': request.args.get('search_user_email', '').strip(),
        'role_name': request.args.get('search_user_role', '').strip(),
        'sale_group_id': request.args.get('search_user_sale_group', default=None, type=int),
        'page': request.args.get('page', 1, type=int),
        'per_page': request.args.get('per_page', 10, type=int)  # Ensure per_page is included in search_params
    }

    is_active_query = request.args.get('search_user_status', '').strip().lower()
    if is_active_query:
        search_params['is_active'] = is_active_query in ['true', '1', 'yes']

    # Cleaning search_params to remove empty entries
    search_params = {k: v for k, v in search_params.items() if v is not None and v != ''}

    api_url = f"{base_url}/users/search/"
    response = requests.get(api_url, params=search_params, headers={'Content-Type': 'application/json'})

    print(f"API Response Status Code: {response.status_code}")
    print(f"API Response Content: {response.text}")

    if response.status_code == 200:
        data = response.json()
        if isinstance(data, dict) and 'users' in data:  # Check if data is a dictionary and contains 'users'
            users = data['users']
            page = data.get('page', 1)
            total_pages = data.get('total_pages', 1)
            total = data.get('total', 0)
            per_page = data.get('per_page', 10)

            # Transform the user data
            transformed_users = []
            for user in users:
                transformed_user = {
                    'id': user['id'],
                    'name': user['name'],
                    'email': user['email'],
                    'roles': [role['name'] for role in user['roles']],
                    'sale_groups': [group['name'] for group in user['sale_groups']],
                    'is_active': user['is_active']
                }
                transformed_users.append(transformed_user)

            return render_template('admin/user_handler_admin.html', users=transformed_users, page=page, total_pages=total_pages, total=total, per_page=per_page)
        else:
            flash('Unexpected data format received from the API.', category='error')
    else:
        flash(f'Failed to fetch user data: {response.reason}', category='error')

    return redirect(url_for('user_api.get_users_admin', page_num=1))
    


@user_api.route('/home', methods=['GET'])
@login_required
def show_favorites():
    user_email = current_user.email  # Assuming you have access to the logged-in user's email
    base_url = current_app.config['BASE_BACKEND_URL']
    api_url = f"{base_url}/favorites/"
    response = requests.get(api_url, params={'user_email': user_email})

    if response.status_code == 200:
        favorite_musics = response.json()
    else:
        flash('Failed to fetch favorites')
        favorite_musics = []

    return render_template('screen/favorites.html', favorite_musics=favorite_musics)



@user_api.route('/admin/users/all/<int:page_num>', methods=['GET'])
@login_required
def get_users_admin(page_num):
    api_url = f"{base_url}/users/all/"
    headers = {'Content-Type': 'application/json'}

    per_page = request.args.get('per_page', 10, type=int)

    response = requests.get(api_url, headers=headers, params={'page': page_num, 'per_page': per_page})
    if response.status_code == 200:
        data = response.json()
        print(data)
        users = data['users']
        total = data['total']
    else:
        flash('Failed to fetch users')
        users = []
        total = 0

    return render_template('admin/user_handler_admin.html', users=users, page=page_num, per_page=per_page, total=total)



# Add new user - Admin role
@ user_api.route('/user/add', methods = ['POST'])
@login_required
async def insert_user():
    ''' Add new user by admin '''
    if request.method == "POST":
        flash("New User Inserted Successfully")
        # Get form car insert pop up table
        name=request.form['username']
        email=request.form['email']
        password=request.form['password']
    

        api_url_create_user = f"{base_url}/users/register/"
        headers_create_user = {'Content-Type': 'application/json'}
        payload_create_user = {'email': email, 'password': password, 'name' : name}

        # Make the POST request
        response_create_user = requests.post(api_url_create_user, json=payload_create_user, headers=headers_create_user)
        print(response_create_user)
        flash('Update Completes')

        return redirect(request.referrer)
    
    

    
# Update user data - Admin role
@user_api.route('/user/update', methods=['GET', 'POST'])
@login_required
async def update_user():
    ''' Admin update user  '''
    # user_role = current_user.role
    # if user_role == 'Admin':
    
    if request.method == 'POST':
        flash("User Updated Successfully")
        

        # Set the new data
        user_id = request.form['id']
        name = request.form['name']
        password = request.form['password']
        email = request.form['email']
        is_active = request.form['is_active']
        

        api_url_create_user = f"{base_url}/users/update/{user_id}"
        headers_create_user = {'Content-Type': 'application/json'}
        payload_create_user = {'email': email, 'password': password, 'name' : name, 'is_active' : is_active}
        

        # Make the POST request
        response_create_user = requests.patch(api_url_create_user, json=payload_create_user, headers=headers_create_user)
        print(response_create_user)
        
        flash('User Update successfull')
        
        return redirect(request.referrer)
    


@user_api.route('/users/delete/<int:user_id>', methods=['GET'])
@login_required
async def delete_role(user_api):
    """ Endpoint to delete a role by an Admin """
    print("role_id: ",user_api)
    api_url = f"{base_url}/roles/delete/{user_api}"
    headers = {'Content-Type': 'application/json'}
    
    response = requests.delete(api_url, headers=headers)
    if response.status_code == 200:
        flash('User deletion successful')
    else:
        flash('User deletion failed')

    return redirect(request.referrer)
