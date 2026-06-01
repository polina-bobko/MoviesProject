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
    Creates and returns a MySQL database connection.

    :raises DBConnectionError: if the connection attempt fails.
    :return: pymysql connection object with DictCursor as default cursor.
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
        raise DBConnectionError(f'Failed to connect to MySQL: {e}')


def fetch_films_by_title(keyword: str, limit: int, offset: int) -> list[dict]:
    """
    Searches for films by keyword in the title and description fields.

    :param keyword: search string (case-insensitive substring match against title and description).
    :param limit: maximum number of records to return.
    :param offset: pagination offset.
    :raises QueryError: if the database query fails.
    :return: list of dicts with fields film_id, title, description.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            pattern = f'%{keyword}%'
            cursor.execute(SELECT_FILMS_BY_TITLE_QUERY, (pattern, pattern, limit, offset))
            return cursor.fetchall()
    except pymysql.Error as e:
        raise QueryError(f'Error querying films by title: {e}')
    finally:
        conn.close()


def fetch_all_genres() -> list[dict]:
    """
    Returns all genres from the category table, sorted by name.

    :raises QueryError: if the database query fails.
    :return: list of dicts with fields category_id, name.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(SELECT_ALL_GENRES_QUERY)
            return cursor.fetchall()
    except pymysql.Error as e:
        raise QueryError(f'Error querying genres: {e}')
    finally:
        conn.close()


def fetch_year_range() -> dict:
    """
    Returns the minimum and maximum release years of films in the database.

    :raises QueryError: if the database query fails.
    :return: dict with fields min_year and max_year.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(SELECT_FILM_YEAR_RANGE_QUERY)
            return cursor.fetchone()
    except pymysql.Error as e:
        raise QueryError(f'Error querying year range: {e}')
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
    Searches for films by genre and release year range.

    :param category_id: genre identifier from the category table.
    :param year_from: lower bound of the year range (inclusive).
    :param year_to: upper bound of the year range (inclusive).
    :param limit: maximum number of records to return.
    :param offset: pagination offset.
    :raises QueryError: if the database query fails.
    :return: list of dicts with fields film_id, title, release_year, description.
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
        raise QueryError(f'Error querying films by genre and year: {e}')
    finally:
        conn.close()