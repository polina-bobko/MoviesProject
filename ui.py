import sys
import logger
import settings
from db import mysql_client, mongo_client

PAGE_SIZE = settings.PAGE_SIZE


# ─────────────────────────────────────────
#  Display helper functions
# ─────────────────────────────────────────

def print_films(films: list[dict], offset: int = 0) -> None:
    """
    Prints a list of films to the console in a readable format.

    :param films: list of dicts with fields title, release_year, description.
    :param offset: pagination offset used for continuous numbering across pages.
    :return: None.
    """
    if not films:
        print('  No films found.')
        return
    for i, film in enumerate(films, offset + 1):
        year = film.get('release_year', '')
        year_str = f' ({year})' if year else ''
        print(f"  {i}. {film['title']}{year_str}")
        if film.get('description'):
            print(f"     {film['description'][:350]}...")
    print()


def ask_for_next_page() -> bool:
    """
    Asks the user whether to display the next page of results.

    :return: True if the user agrees, False otherwise.
    """
    answer = input('Show next 10 results? (y/n yes/no): ').strip().lower()
    return answer in ('д', 'y', 'yes', 'да', '')


# ─────────────────────────────────────────
#  Search by keyword
# ─────────────────────────────────────────

@logger.logger_decorator
def handle_search_movies_by_keyword() -> None:
    """
    Handles film search by keyword in the title.
    Prompts the user for a string, displays results page by page
    in batches of PAGE_SIZE, and saves the query to MongoDB.

    :return: None.
    """
    keyword = input('Enter a keyword to search by title or description: ').strip()
    if not keyword:
        print('Search query cannot be empty.')
        return

    mongo_client.save_query('by_keyword', {'keyword': keyword})

    offset = 0
    while True:
        films = mysql_client.fetch_films_by_title(keyword, PAGE_SIZE, offset)
        print_films(films, offset)

        if len(films) < PAGE_SIZE:
            print('These are all the results.')
            break

        if not ask_for_next_page():
            break
        offset += PAGE_SIZE


# ─────────────────────────────────────────
#  Search by genre and year range
# ─────────────────────────────────────────

@logger.logger_decorator
def handle_search_movies_by_genre() -> None:
    """
    Handles film search by genre and release year range.
    Before input, shows the user the list of available genres and
    the valid year range. Results are displayed page by page in
    batches of PAGE_SIZE. The query is saved to MongoDB.

    :return: None.
    """
    genres = mysql_client.fetch_all_genres()
    if not genres:
        print('Failed to load genres.')
        return

    print('\nAvailable genres:')
    genre_map = {}
    for g in genres:
        print(f"  {g['category_id']}. {g['name']}")
        genre_map[str(g['category_id'])] = g

    year_range = mysql_client.fetch_year_range()
    min_year = year_range['min_year']
    max_year = year_range['max_year']
    print(f'\nFilm release years in the database: from {min_year} to {max_year}')

    genre_id_input = input('\nEnter genre number: ').strip()
    if genre_id_input not in genre_map:
        print('Invalid genre number.')
        return
    selected_genre = genre_map[genre_id_input]

    try:
        year_from_input = input(f'Year from ({min_year}–{max_year}): ').strip()
        year_from = int(year_from_input) if year_from_input else min_year

        year_to_input = input(f'Year to ({min_year}–{max_year}): ').strip()
        year_to = int(year_to_input) if year_to_input else max_year
    except ValueError:
        print('Invalid year format.')
        return

    if not (min_year <= year_from <= max_year and min_year <= year_to <= max_year):
        print(f'Year must be in the range {min_year}–{max_year}.')
        return

    if year_from > year_to:
        year_from, year_to = year_to, year_from

    mongo_client.save_query('by_genre_and_year', {
        'genre_id': selected_genre['category_id'],
        'genre_name': selected_genre['name'],
        'year_from': year_from,
        'year_to': year_to,
    })

    print(f'\nFilms in genre "{selected_genre["name"]}" ({year_from}–{year_to}):\n')

    offset = 0
    while True:
        films = mysql_client.fetch_films_by_genre_and_year(
            selected_genre['category_id'], year_from, year_to, PAGE_SIZE, offset
        )
        print_films(films, offset)

        if len(films) < PAGE_SIZE:
            print('These are all the results.')
            break

        if not ask_for_next_page():
            break
        offset += PAGE_SIZE


# ─────────────────────────────────────────
#  Popular queries
# ─────────────────────────────────────────

def _format_query_doc(doc: dict, show_count: bool = False) -> str:
    """
    Formats a MongoDB document into a human-readable string.

    :param doc: dict with fields _id (type + params), count, last_used.
    :param show_count: if True — shows the number of repetitions,
                       if False — shows the date of last use.
    :return: formatted string describing the query.
    """
    query_type = doc['_id']['type']
    params = doc['_id']['params']

    if query_type == 'by_keyword':
        label = f"By keyword: \"{params.get('keyword', '?')}\""
    elif query_type == 'by_genre_and_year':
        label = (
            f"By genre \"{params.get('genre_name', '?')}\" "
            f"({params.get('year_from', '?')}–{params.get('year_to', '?')})"
        )
    else:
        label = f"{query_type}: {params}"

    suffix = f"  — {doc['count']} time(s)" if show_count else f"  — {doc['last_used'].strftime('%d.%m.%Y %H:%M')}"
    return label + suffix


@logger.logger_decorator
def handle_popular_queries_by_date() -> None:
    """
    Displays the 5 most recent unique search queries, sorted by date.

    :return: None.
    """
    results = mongo_client.fetch_popular_by_date(limit=5)
    if not results:
        print('Query history is empty.')
        return
    print('\nLast 5 unique queries:\n')
    for i, doc in enumerate(results, 1):
        print(f'  {i}. {_format_query_doc(doc, show_count=False)}')
    print()


@logger.logger_decorator
def handle_popular_queries_by_number() -> None:
    """
    Displays the top 5 search queries sorted by frequency of use.

    :return: None.
    """
    results = mongo_client.fetch_popular_by_frequency(limit=5)
    if not results:
        print('Query history is empty.')
        return
    print('\nTop 5 queries by frequency:\n')
    for i, doc in enumerate(results, 1):
        print(f'  {i}. {_format_query_doc(doc, show_count=True)}')
    print()


# ─────────────────────────────────────────
#  Menu configuration
# ─────────────────────────────────────────

menu_config = {
    'title': 'Main menu',
    'items': {
        '1': {
            'text': 'Search films',
            'submenu': {
                'title': 'Film search menu',
                'items': {
                    '1': {'text': 'Search by keyword', 'action': handle_search_movies_by_keyword},
                    '2': {'text': 'Search by genre and year', 'action': handle_search_movies_by_genre},
                    '0': {'text': 'Back', 'action': 'back'},
                },
            },
        },
        '2': {
            'text': 'Popular queries',
            'submenu': {
                'title': 'Popular queries menu',
                'items': {
                    '1': {'text': 'By date (most recent)', 'action': handle_popular_queries_by_date},
                    '2': {'text': 'By frequency', 'action': handle_popular_queries_by_number},
                    '0': {'text': 'Back', 'action': 'back'},
                },
            },
        },
        '0': {
            'text': 'Exit',
            'action': lambda: sys.exit(0),
        },
    },
}


# ─────────────────────────────────────────
#  Menu engine
# ─────────────────────────────────────────

def run_menu(config: dict) -> None:
    """
    Runs the interactive console menu loop.
    Supports nested submenus via a stack and a 'back' action to return.

    :param config: menu configuration dict with fields title and items.
    :return: None.
    """
    stack = [config]

    while stack:
        current_menu = stack[-1]
        print(f'\n=== {current_menu.get("title", "Menu")} ===')

        for key, value in current_menu['items'].items():
            print(f'  {key}: {value["text"]}')

        choice = input('\nSelect menu item: ').strip()

        if choice in current_menu['items']:
            menu_item = current_menu['items'][choice]
            if menu_item.get('action') == 'back':
                stack.pop()
            elif 'submenu' in menu_item:
                stack.append(menu_item['submenu'])
            elif 'action' in menu_item:
                try:
                    menu_item['action']()
                except Exception as e:
                    print(f'Error: {e}')
        else:
            print('Invalid input. Please try again.')