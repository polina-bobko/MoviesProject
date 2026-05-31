from datetime import datetime, timezone
from pymongo import MongoClient
from pymongo.collection import Collection
import settings
from errors import MongoConnectionError
from logger import logger


def get_collection() -> Collection:
    """
    Создаёт подключение к MongoDB и возвращает коллекцию для хранения запросов.

    :raises MongoConnectionError: если подключение к MongoDB не удалось.
    :return: объект коллекции pymongo.
    """
    try:
        client = MongoClient(settings.MONGO_URL, serverSelectionTimeoutMS=3000)
        client.server_info()
        db = client[settings.MONGO_DB]
        return db[settings.MONGO_COLLECTION]
    except Exception as e:
        raise MongoConnectionError(f'Не удалось подключиться к MongoDB: {e}')


def save_query(query_type: str, params: dict) -> None:
    """
    Сохраняет поисковый запрос пользователя в MongoDB.

    :param query_type: тип запроса, например 'by_keyword' или 'by_genre_and_year'.
    :param params: словарь с параметрами запроса (ключевое слово, жанр, годы и т.д.).
    :return: None. При недоступности MongoDB ошибка логируется и выполнение продолжается.
    """
    try:
        collection = get_collection()
        document = {
            'type': query_type,
            'params': params,
            'created_at': datetime.now(timezone.utc),
        }
        collection.insert_one(document)
        logger.info(f'Запрос сохранён в MongoDB: {query_type}')
    except MongoConnectionError as e:
        logger.error(f'MongoDB недоступна, запрос не сохранён: {e}')


def fetch_popular_by_frequency(limit: int = 5) -> list[dict]:
    """
    Возвращает наиболее часто повторяющиеся поисковые запросы.

    :param limit: количество возвращаемых записей (по умолчанию 5).
    :raises MongoConnectionError: если подключение к MongoDB не удалось.
    :return: список словарей с полями _id (type + params), count, last_used,
             отсортированных по убыванию count.
    """
    try:
        collection = get_collection()
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
        logger.error(f'Ошибка получения популярных запросов: {e}')
        return []


def fetch_popular_by_date(limit: int = 5) -> list[dict]:
    """
    Возвращает последние уникальные поисковые запросы, отсортированные по дате.

    :param limit: количество возвращаемых записей (по умолчанию 5).
    :raises MongoConnectionError: если подключение к MongoDB не удалось.
    :return: список словарей с полями _id (type + params) и last_used,
             отсортированных по убыванию даты последнего использования.
    """
    try:
        collection = get_collection()
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
        logger.error(f'Ошибка получения последних запросов: {e}')
        return []