# ./backend/module/user_api.py
from fastapi import APIRouter, HTTPException
from model.users import User, UpdateUser, LoginCredentials, UserResponse
from model.musics import Music, MusicResponse
import boto3
from boto3.dynamodb.conditions import Key, Attr
from typing import Optional, List
from fastapi.encoders import jsonable_encoder
import logging
from fastapi import Query
import uuid
from fastapi.responses import JSONResponse

router = APIRouter()

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
login_table = dynamodb.Table('login')  # Reference to the 'login' table
favorites_table = dynamodb.Table('user_favorites')  # Reference to the 'user_favorites' table
music_table = dynamodb.Table('music')  # Reference to the 'music' table



@router.post("/register/", response_model=UserResponse)
def register_user(user: User):
    try:
        # Check if the user already exists by scanning the table for the email
        response = login_table.scan(
            FilterExpression=Attr('email').eq(user.email)
        )
        
        if response.get('Items'):
            return JSONResponse(status_code=400, content={"message": "User with this email already exists"})

        # Generate a unique user_id
        user_id = str(uuid.uuid4())

        # If the user doesn't exist, add them to the table
        login_table.put_item(
            Item={
                'user_id': user_id,  # Add the generated user_id
                'email': user.email,
                'user_name': user.user_name,
                'password': user.password  # Since you mentioned you don't need to hash the password
            }
        )

        return UserResponse(email=user.email, user_name=user.user_name)
    
    except Exception as e:
        logging.error(f"Error in register_user: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")





@router.get("/favorites/search/", response_model=MusicResponse)
async def search_subscribed_music(
    user_email: str,
    search_music_title: Optional[str] = Query(None),
    search_music_artist: Optional[str] = Query(None),
    search_music_year: Optional[str] = Query(None)
):
    try:
        # Get user_id based on email
        user_id = get_user_id_from_email(user_email)
        logging.debug(f"User ID: {user_id}")

        # Query the user's subscribed music IDs
        response = favorites_table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        favorite_music_ids = [item['music_id'] for item in response.get('Items', [])]
        logging.debug(f"Favorite Music IDs: {favorite_music_ids}")

        if not favorite_music_ids:
            return {"musics": [], "total": 0}

        # Filter by title, artist, and year if provided
        filter_expression = Attr('music_id').is_in(favorite_music_ids)
        if search_music_title:
            filter_expression &= Attr('title').contains(search_music_title)
        if search_music_artist:
            filter_expression &= Attr('artist').contains(search_music_artist)
        if search_music_year:
            filter_expression &= Attr('year').eq(search_music_year)

        logging.debug(f"Filter Expression: {filter_expression}")

        musics = music_table.scan(
            FilterExpression=filter_expression
        ).get('Items', [])
        print(musics)
        total_items = len(musics)

        if total_items == 0:
            return JSONResponse(content={"message": "Music not found"}, status_code=404)

        return {"musics": musics, "total": total_items}

    except Exception as e:
        logging.error(f"Error in search_subscribed_music: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))




@router.delete("/favorites/remove/")
def remove_from_favorites(user_email: str, music_id: str):
    logging.debug(f"Removing from favorites: User email: {user_email}, Music ID: {music_id}")
    try:
        # Get the user ID based on user email
        user_id = get_user_id_from_email(user_email)

        # Check if the entry exists
        existing_entry = favorites_table.get_item(
            Key={'user_id': user_id, 'music_id': music_id}
        )
        if 'Item' not in existing_entry:
            logging.info("Item does not exist in favorites")
            return JSONResponse(status_code=400, content={"message": "Music not found in favorites"})

        # Remove from favorites
        result = favorites_table.delete_item(
            Key={
                'user_id': user_id,
                'music_id': music_id
            }
        )
        logging.debug(f"Removed from favorites successfully: {result}")
        return JSONResponse(content={"message": "Removed from favorites successfully"})

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return JSONResponse(status_code=500, content={"message": "An error occurred", "details": str(e)})



@router.post("/favorites/add/")
async def add_to_favorites(user_email: str, music_id: str):
    logging.debug(f"Adding to favorites: User email: {user_email}, Music ID: {music_id}")
    try:
        # Get the user ID based on user email - assuming you have a way to resolve user_id from user_email
        user_id = get_user_id_from_email(user_email)  # Implement this function based on your user management

        # Check if the entry already exists
        existing_entry = favorites_table.get_item(
            Key={'user_id': user_id, 'music_id': music_id}
        )
        if 'Item' in existing_entry:
            logging.info("Item already exists in favorites")
            return JSONResponse(status_code=200, content={"message": "This music has already been added to your favorites."})

        # Add to favorites
        result = favorites_table.put_item(
            Item={
                'user_id': user_id,
                'music_id': music_id
            }
        )
        logging.debug(f"Added to favorites successfully: {result}")
        return JSONResponse(content={"message": "Music added to favorites successfully"})

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        return JSONResponse(status_code=500, content={"message": "An error occurred", "details": str(e)})
    
    
    
def get_user_id_from_email(email: str) -> str:
    """
    Fetch user_id from the 'login' table based on the email address.
    Assumes there is a GSI for email named 'EmailIndex'.
    """
    try:
        response = login_table.query(
            IndexName='EmailIndex',  # This should be set on your DynamoDB 'login' table if you're querying by email
            KeyConditionExpression=Key('email').eq(email)
        )
        if not response['Items']:
            raise HTTPException(status_code=404, detail="User not found")

        # Assuming the user_id is stored in the 'user_id' field
        return response['Items'][0]['user_id']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user ID: {str(e)}")
    
    

@router.get("/favorites/")
async def get_favorites(user_email: str, page: int = 1, per_page: int = 10):
    try:
        user_id = get_user_id_from_email(user_email)

        # Query the user_favorites table to get the music IDs
        response = favorites_table.query(
            KeyConditionExpression=Key('user_id').eq(user_id)
        )
        favorite_music_ids = [item['music_id'] for item in response.get('Items', [])]

        # Pagination logic
        total_items = len(favorite_music_ids)
        start = (page - 1) * per_page
        end = start + per_page
        paginated_ids = favorite_music_ids[start:end]

        # Fetch the music details from the music table
        favorite_music_details = []
        for music_id in paginated_ids:
            music_response = music_table.get_item(Key={'music_id': music_id})
            if 'Item' in music_response:
                favorite_music_details.append(music_response['Item'])

        return {"favorites": favorite_music_details, "total": total_items}

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



    

# Login
@router.post("/login/", response_model=UserResponse)
def login_user(credentials: LoginCredentials):
    email = credentials.email
    password = credentials.password
    try:
        response = login_table.query(
            IndexName='EmailIndex',
            KeyConditionExpression=Key('email').eq(email)
        )
        if not response['Items']:
            raise HTTPException(status_code=404, detail="User not found")

        user = response['Items'][0]
        if user['password'] != password:
            raise HTTPException(status_code=401, detail="Invalid password")

        return UserResponse(email=user['email'], user_name=user['user_name'])
    except Exception as e:
        logging.error(f"Error during login: {e}")
        raise HTTPException(status_code=500, detail=f"Error during login: {str(e)}")



@router.get("/favorites/{user_email}", response_model=List[Music])
def get_user_favorites(user_email: str):
    try:
        # Get favorite music IDs for the user
        response = favorites_table.query(
            IndexName='user_email-index',
            KeyConditionExpression=Key('user_email').eq(user_email)
        )
        favorite_music_ids = [item['music_id'] for item in response.get('Items', [])]

        # Fetch music details for each ID
        favorites = []
        for music_id in favorite_music_ids:
            music_response = music_table.get_item(Key={'id': music_id})
            if 'Item' in music_response:
                favorites.append(Music(**music_response['Item']))

        return favorites
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# Get all users
@router.get("/users/", response_model=List[User])
def get_all_users():
    print(f"Accessing DynamoDB Table: {login_table.name} in Region: {dynamodb.meta}")
    try:
        response = login_table.scan()
        users = response.get('Items', [])
        return [User(**user) for user in users]
    except Exception as e:
        error_msg = f"Error accessing DynamoDB: {str(e)}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)



# Create user
@router.post("/users/", response_model=User)
def create_user(user: User):
    existing_user = login_table.get_item(Key={'email': user.email})
    if 'Item' in existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    login_table.put_item(Item=user.dict())
    return user



# Get user by email
@router.get("/users/{email}", response_model=User)
def read_user(email: str):
    response = login_table.get_item(Key={'email': email})
    if 'Item' not in response:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**response['Item'])


# Update user
@router.put("/users/{email}", response_model=User)
def update_user(email: str, user: UpdateUser):
    response = login_table.get_item(Key={'email': email})
    if 'Item' not in response:
        raise HTTPException(status_code=404, detail="User not found")
    updated_data = response['Item']
    if user.user_name:
        updated_data['user_name'] = user.user_name
    if user.password:
        updated_data['password'] = user.password
    login_table.put_item(Item=updated_data)
    return User(**updated_data)


# Delete user
@router.delete("/users/{email}", response_model=dict)
def delete_user(email: str):
    response = login_table.get_item(Key={'email': email})
    if 'Item' not in response:
        raise HTTPException(status_code=404, detail="User not found")
    login_table.delete_item(Key={'email': email})
    return {"message": "User deleted successfully"}



@router.get("/users/{email}", response_model=User)
def get_user_by_email(email: str):
    response = login_table.get_item(Key={'email': email})
    if 'Item' not in response:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**response['Item'])


