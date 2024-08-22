import boto3
from boto3.dynamodb.conditions import Key
import pandas as pd
import json
import requests
from io import BytesIO
import uuid  # Import UUID library to generate unique IDs



def initialize_aws_services():
    """Initialize and return AWS DynamoDB and S3 clients."""
    dynamodb = boto3.resource('dynamodb')
    s3 = boto3.client('s3')
    return dynamodb, s3



def table_exists(dynamodb, table_name):
    """Check if a DynamoDB table exists."""
    try:
        dynamodb.Table(table_name).load()
        return True
    except dynamodb.meta.client.exceptions.ResourceNotFoundException:
        return False



def create_table(dynamodb, table_name, key_schema, attribute_definitions, provisioned_throughput, gsi=None):
    """Create a DynamoDB table if it does not already exist."""
    if not table_exists(dynamodb, table_name):
        params = {
            'TableName': table_name,
            'KeySchema': key_schema,
            'AttributeDefinitions': attribute_definitions,
            'ProvisionedThroughput': provisioned_throughput
        }
        if gsi:
            params['GlobalSecondaryIndexes'] = gsi
        table = dynamodb.create_table(**params)
        table.meta.client.get_waiter('table_exists').wait(TableName=table_name)
        print(f'{table_name} table created.')
        return table
    else:
        print(f'{table_name} table already exists.')
        return dynamodb.Table(table_name)



def load_data_to_dynamodb(dynamodb, table_name, data):
    """Load data into a DynamoDB table using batch writer, checking for duplicates."""
    table = dynamodb.Table(table_name)
    with table.batch_writer() as batch:
        for item in data:
            if table_name == 'login':
                item_key = 'user_id'
            else:
                item_key = 'music_id'
            response = table.query(KeyConditionExpression=Key(item_key).eq(item[item_key]))
            if response['Count'] == 0:
                batch.put_item(Item=item)
    print(f"Data has been inserted into {table_name}.")



def download_image(url):
    """Download an image from a URL and return it as a bytes object."""
    response = requests.get(url)
    response.raise_for_status()
    return BytesIO(response.content)



def upload_image_to_s3(s3, bucket_name, file_name, image_data):
    """Upload an image to an S3 bucket into a specified folder."""
    folder_path = f"music_image_url/{file_name}"
    s3.upload_fileobj(
        image_data,
        bucket_name,
        folder_path,
        ExtraArgs={
            'ContentType': 'image/jpeg',
            'ACL': 'public-read'
        }
    )
    print(f"Uploaded {file_name} to S3 bucket {bucket_name} in folder music_image_url")



def process_images(s3, bucket_name, music_data):
    """Process images from music data and upload to S3 within a specific folder."""
    for song in music_data:
        image_url = song['img_url']
        artist = song['artist']
        file_name = f"{artist.replace(' ', '_')}.jpg"
        try:
            image_data = download_image(image_url)
            upload_image_to_s3(s3, bucket_name, file_name, image_data)
        except requests.RequestException as e:
            print(f"Failed to download image from {image_url}: {e}")
        except boto3.exceptions.S3UploadFailedError as e:
            print(f"Failed to upload {file_name} to S3: {e}")



def main():
    """Main function to orchestrate the AWS operations."""
    dynamodb, s3 = initialize_aws_services()

    # Modify table creation to include user_id and music_id
    create_table(dynamodb, 'music', [{'AttributeName': 'music_id', 'KeyType': 'HASH'}], [{'AttributeName': 'music_id', 'AttributeType': 'S'}], {'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1})
    
    # Create 'login' table with GSI for email querying
    email_index = {
        'IndexName': 'EmailIndex',
        'KeySchema': [{'AttributeName': 'email', 'KeyType': 'HASH'}],
        'Projection': {'ProjectionType': 'ALL'},
        'ProvisionedThroughput': {'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
    }
    create_table(dynamodb, 'login', 
                 [{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
                 [{'AttributeName': 'user_id', 'AttributeType': 'S'}, {'AttributeName': 'email', 'AttributeType': 'S'}],
                 {'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1},
                 gsi=[email_index])
    

    # Create user_favorites table using user_id and music_id
    create_table(dynamodb, 'user_favorites',
        [
            {'AttributeName': 'user_id', 'KeyType': 'HASH'},  # Partition key
            {'AttributeName': 'music_id', 'KeyType': 'RANGE'}  # Sort key
        ],
        [
            {'AttributeName': 'user_id', 'AttributeType': 'S'},
            {'AttributeName': 'music_id', 'AttributeType': 'S'}
        ],
        {'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
    )

    # Load data using UUIDs
    file_path = 'login.csv'
    login_data = pd.read_csv(file_path, delimiter='\t')
    formatted_login_data = [{'user_id': str(uuid.uuid4()), 'email': row['email'].strip(), 'user_name': row['user_name'].strip(), 'password': row['password'].strip()} for index, row in login_data.iterrows()]
    load_data_to_dynamodb(dynamodb, 'login', formatted_login_data)

    music_file_path = 'a2.json'
    with open(music_file_path, 'r') as file:
        music_data = json.load(file)['songs']
        formatted_music_data = [{'music_id': str(uuid.uuid4()), 'title': song['title'], 'artist': song['artist'], 'year': song['year'], 'web_url': song['web_url'], 'img_url': song['img_url']} for song in music_data]
    load_data_to_dynamodb(dynamodb, 'music', formatted_music_data)

    # S3 image uploading
    bucket_name = 'aws-cloud-computing'  # Replace with your actual S3 bucket name
    process_images(s3, bucket_name, formatted_music_data)



if __name__ == "__main__":
    main()
