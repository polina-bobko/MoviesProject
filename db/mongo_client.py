from datetime import datetime
from pymongo import MongoClient
import settings
from errors import MongoConnectionError
from logger import logger


def _get_client() -> MongoClient:
    """
    Creates and returns a MongoDB client.

    :raises MongoConnectionError: if the connection attempt fails.
    :return: MongoClient object.
    """
    try:
        client = MongoClient(settings.MONGO_URL, serverSelectionTimeoutMS=3000)
        client.server_info()
        return client
    except Exception as e:
        raise MongoConnectionError(f'Failed to connect to MongoDB: {e}')


def save_query(query_type: str, params: dict) -> None:
    """
    Saves a user search query to MongoDB.

    :param query_type: type of query, e.g. 'by_keyword' or 'by_genre_and_year'.
    :param params: dict of query parameters (keyword, genre, years, etc.).
    :return: None. If MongoDB is unavailable, the error is logged and execution continues.
    """
    try:
        with _get_client() as client:
            collection = client[settings.MONGO_DB][settings.MONGO_COLLECTION]
            document = {
                'type': query_type,
                'params': params,
                'created_at': datetime.now(),
            }
            collection.insert_one(document)
            logger.info(f'Query saved to MongoDB: {query_type}')
    except MongoConnectionError as e:
        logger.error(f'MongoDB unavailable, query not saved: {e}')


def fetch_popular_by_frequency(limit: int = 5) -> list[dict]:
    """
    Returns the most frequently repeated search queries.

    :param limit: number of records to return (default 5).
    :raises MongoConnectionError: if the connection to MongoDB fails.
    :return: list of dicts with fields _id (type + params), count, last_used,
             sorted by count descending.
    """
    try:
        with _get_client() as client:
            collection = client[settings.MONGO_DB][settings.MONGO_COLLECTION]
            pipeline = [
                {
                    '$group': {
                        '_id': {
                            'type': '$type',
                            'params': '$params',
                        },
                        'count': {'$sum': 1},
                        'last_used': {'$max': '$created_at'},
                    }
                },
                {'$sort': {'count': -1}},
                {'$limit': limit},
            ]
            return list(collection.aggregate(pipeline))
    except MongoConnectionError as e:
        logger.error(f'Error fetching popular queries: {e}')
        return []


def fetch_popular_by_date(limit: int = 5) -> list[dict]:
    """
    Returns the most recent unique search queries, sorted by date.

    :param limit: number of records to return (default 5).
    :raises MongoConnectionError: if the connection to MongoDB fails.
    :return: list of dicts with fields _id (type + params) and last_used,
             sorted by last_used descending.
    """
    try:
        with _get_client() as client:
            collection = client[settings.MONGO_DB][settings.MONGO_COLLECTION]
            pipeline = [
                {'$sort': {'created_at': -1}},
                {
                    '$group': {
                        '_id': {
                            'type': '$type',
                            'params': '$params',
                        },
                        'last_used': {'$first': '$created_at'},
                    }
                },
                {'$sort': {'last_used': -1}},
                {'$limit': limit},
            ]
            return list(collection.aggregate(pipeline))
    except MongoConnectionError as e:
        logger.error(f'Error fetching recent queries: {e}')
        return []