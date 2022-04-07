import logging

import googleapiclient.discovery
import googleapiclient.errors
from django.conf import settings
from youtube_title_parse import get_artist_title

# logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
from youtubesearchpython import VideosSearch

"""
This module handles YouTube search API functionality.
"""


class YouTubeSearchError(Exception):
    pass


def perform_search(query: str, page_token=None):
    """
    Executes YouTube search request using YouTube Data API v3 and returns
    simplified list of video results.

    :param query: Query string
    :param page_token: Page token
    """
    # api_service_name = "youtube"
    # api_version = "v3"

    # if not settings.YOUTUBE_API_KEY:
    #     raise YouTubeSearchError(
    #         'Missing YouTube Data API key. Please set the YOUTUBE_API_KEY env variable or update settings.py.')
    #
    # youtube = googleapiclient.discovery.build(
    #     api_service_name,
    #     api_version,
    #     developerKey=settings.YOUTUBE_API_KEY,
    #     cache_discovery=False)
    #
    # # Execute search query
    # search_request = youtube.search().list(part="snippet",
    #                                        maxResults=25,
    #                                        q=query,
    #                                        pageToken=page_token)
    # search_result = search_request.execute()
    # search_items = search_result['items']
    #
    # # Construct list of eligible video IDs
    # ids = [
    #     item['id']['videoId'] for item in search_items
    #     if item['id']['kind'] == 'youtube#video'
    #        and item['snippet']['liveBroadcastContent'] == 'none'
    # ]
    # # Make request to videos() in order to retrieve the durations
    # duration_request = youtube.videos().list(part='contentDetails', id=','.join(ids))
    # duration_result = duration_request.execute()
    # duration_items = duration_result['items']
    # duration_dict = {
    #     item['id']: item['contentDetails']['duration']
    #     for item in duration_items
    # }
    videosSearch = VideosSearch(query, limit=25)
    search_items = videosSearch.result()['result']

    # Merge results into single, simplified list
    videos = []
    for item in search_items:
        if item['type'] == 'video':
            parsed_artist = None
            parsed_title = None
            result = get_artist_title(item['title'])

            if result:
                parsed_artist, parsed_title = result
            else:
                parsed_artist = item['channel']['name']
                parsed_title = item['title']

            videos.append(
                {
                    'id': item['id'],
                    'title': item['title'],
                    'parsed_artist': parsed_artist,
                    'parsed_title': parsed_title,
                    'channel': item['channel']['name'],
                    'thumbnail': item['thumbnails'][0]['url'],
                    'duration': item['duration']
                }
            )

    next_page_token = None
    # Return next page token and video result
    return next_page_token, videos
