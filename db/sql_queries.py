SELECT_FILMS_BY_TITLE_QUERY = """
    SELECT film_id, title, description
    FROM film
    WHERE LOWER(title) LIKE LOWER(%s)
    OR LOWER(description) LIKE LOWER(%s)
    ORDER BY title
    LIMIT %s OFFSET %s;
"""

SELECT_ALL_GENRES_QUERY = """
    SELECT category_id, name
    FROM category
    ORDER BY name;
"""

SELECT_FILM_YEAR_RANGE_QUERY = """
    SELECT MIN(release_year) AS min_year,
           MAX(release_year) AS max_year
    FROM film;
"""

SELECT_FILMS_BY_GENRE_AND_YEAR_QUERY = """
    SELECT DISTINCT f.film_id,
           f.title,
           f.release_year,
           f.description
    FROM film f
    JOIN film_category fc
        ON fc.film_id = f.film_id
    WHERE fc.category_id = %s
      AND f.release_year BETWEEN %s AND %s
    ORDER BY f.release_year, f.title
    LIMIT %s OFFSET %s;
"""