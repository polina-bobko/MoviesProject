import pymysql
import pymysql.cursors
import settings
from errors import DBConnectionError, QueryError
from db.sql_queries import (
    SELECT_FILMS_BY_TITLE_QUERY,
    SELECT_ALL_GENRES_QUERY,
    SELECT_FILM_YEAR_RANGE_QUERY,
    SELECT_FILMS_BY_GENRE_AND_YEAR_QUERY,
)


def get_connection() -> pymysql.connections.Connection:
    """
    Создаёт и возвращает соединение с базой данных MySQL.

    :raises DBConnectionError: если подключение не удалось.
    :return: объект соединения pymysql с DictCursor по умолчанию.
    """
    try:
        conn = pymysql.connect(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD,
            database=settings.DB_NAME,
            cursorclass=pymysql.cursors.DictCursor,
        )
        return conn
    except pymysql.Error as e:
        raise DBConnectionError(f'Не удалось подключиться к MySQL: {e}')


def fetch_films_by_title(keyword: str, limit: int, offset: int) -> list[dict]:
    """
    Ищет фильмы по ключевому слову в названии.

    :param keyword: строка поиска (ищется вхождение в title без учёта регистра).
    :param limit: максимальное количество возвращаемых записей.
    :param offset: смещение для пагинации.
    :raises QueryError: если запрос к базе завершился ошибкой.
    :return: список словарей с полями film_id, title, description.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(SELECT_FILMS_BY_TITLE_QUERY, (f'%{keyword}%', limit, offset))
            return cursor.fetchall()
    except pymysql.Error as e:
        raise QueryError(f'Ошибка запроса фильмов по названию: {e}')
    finally:
        conn.close()


def fetch_all_genres() -> list[dict]:
    """
    Возвращает все жанры из таблицы category, отсортированные по названию.

    :raises QueryError: если запрос к базе завершился ошибкой.
    :return: список словарей с полями category_id, name.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(SELECT_ALL_GENRES_QUERY)
            return cursor.fetchall()
    except pymysql.Error as e:
        raise QueryError(f'Ошибка запроса жанров: {e}')
    finally:
        conn.close()


def fetch_year_range() -> dict:
    """
    Возвращает минимальный и максимальный год выпуска фильмов в базе.

    :raises QueryError: если запрос к базе завершился ошибкой.
    :return: словарь с полями min_year и max_year.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(SELECT_FILM_YEAR_RANGE_QUERY)
            return cursor.fetchone()
    except pymysql.Error as e:
        raise QueryError(f'Ошибка запроса диапазона годов: {e}')
    finally:
        conn.close()


def fetch_films_by_genre_and_year(
    category_id: int,
    year_from: int,
    year_to: int,
    limit: int,
    offset: int,
) -> list[dict]:
    """
    Ищет фильмы по жанру и диапазону годов выпуска.

    :param category_id: идентификатор жанра из таблицы category.
    :param year_from: нижняя граница диапазона годов (включительно).
    :param year_to: верхняя граница диапазона годов (включительно).
    :param limit: максимальное количество возвращаемых записей.
    :param offset: смещение для пагинации.
    :raises QueryError: если запрос к базе завершился ошибкой.
    :return: список словарей с полями film_id, title, release_year, description.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                SELECT_FILMS_BY_GENRE_AND_YEAR_QUERY,
                (category_id, year_from, year_to, limit, offset),
            )
            return cursor.fetchall()
    except pymysql.Error as e:
        raise QueryError(f'Ошибка запроса фильмов по жанру и году: {e}')
    finally:
        conn.close()