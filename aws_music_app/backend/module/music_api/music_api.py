# ./backend/module/music_api.py
from fastapi import APIRouter, HTTPException, Query
from model.musics import Music, MusicResponse
import boto3
from boto3.dynamodb.conditions import Key, Attr
from typing import Optional, List
from fastapi.encoders import jsonable_encoder
import logging

router = APIRouter()

# Initialize DynamoDB
dynamodb = boto3.resource('dynamodb')
music_table  = dynamodb.Table('music')  # Ensure this table is created in DynamoDB


# Get all music
@router.get("/musics/all/", response_model=List[Music])
def get_all_music():
    try:
        response = music_table.scan()  # Scans the entire table, consider using pagination in production
        music_items = response.get('Items', [])
        return [Music(**item) for item in music_items]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    
    
@router.get("/musics/unsubscribed/", response_model=MusicResponse)
async def search_unsubscribed_music(
    search_music_title: Optional[str] = Query(None),
    search_music_artist: Optional[str] = Query(None),
    search_music_year: Optional[str] = Query(None),
    page: int = 1,
    per_page: int = 10
):
    try:
        filter_expression = None

        if search_music_title:
            filter_expression = Attr('title').contains(search_music_title)
        if search_music_artist:
            if filter_expression:
                filter_expression = filter_expression & Attr('artist').contains(search_music_artist)
            else:
                filter_expression = Attr('artist').contains(search_music_artist)
        if search_music_year:
            if filter_expression:
                filter_expression = filter_expression & Attr('year').eq(search_music_year)
            else:
                filter_expression = Attr('year').eq(search_music_year)
        
        logging.debug(f"Filter Expression: {filter_expression}")

        musics = []
        last_evaluated_key = None

        # Paginate until we reach the desired page
        while page > 0:
            scan_params = {
                'Limit': per_page
            }
            if filter_expression:
                scan_params['FilterExpression'] = filter_expression
            if last_evaluated_key:
                scan_params['ExclusiveStartKey'] = last_evaluated_key
            
            response = music_table.scan(**scan_params)
            last_evaluated_key = response.get('LastEvaluatedKey', None)
            
            if page == 1:
                musics = response.get('Items', [])
                break
            else:
                page -= 1

        # Count total items matching the filter
        total_items = music_table.scan(
            FilterExpression=filter_expression if filter_expression else Attr('music_id').exists(),
            Select='COUNT'
        ).get('Count', 0)
        
        return {"musics": musics, "total": total_items}

    except Exception as e:
        logging.error(f"Error in search_unsubscribed_music: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))






