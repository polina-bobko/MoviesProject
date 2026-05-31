import sys
import logger
import settings
from db import mysql_client, mongo_client

PAGE_SIZE = settings.PAGE_SIZE


# ─────────────────────────────────────────
#  Вспомогательные функции отображения
# ─────────────────────────────────────────


def print_films(films: list[dict], offset: int = 0) -> None:
    """
    Выводит список фильмов в консоль в читаемом формате.

    :param films: список словарей с полями title, release_year, description.
    :param offset: смещение для сквозной нумерации при пагинации.
    :return: None.
    """
    if not films:
        print('  Фильмов не найдено.')
        return
    for i, film in enumerate(films, offset + 1):
        year = film.get('release_year', '')
        year_str = f' ({year})' if year else ''
        print(f"  {i}. {film['title']}{year_str}")
        if film.get('description'):
            print(f"     {film['description'][:200]}...")
    print()

def ask_for_next_page() -> bool:
    """
    Спрашивает пользователя, показать ли следующую страницу результатов.

    :return: True, если пользователь согласен, False — если нет.
    """
    answer = input('Показать следующие 10 результатов? (д/н y/n yes/no): ').strip().lower()
    return answer in ('д', 'y', 'yes', 'да', '')


# ─────────────────────────────────────────
#  Поиск по ключевому слову
# ─────────────────────────────────────────

@logger.logger_decorator
def handle_search_movies_by_keyword() -> None:
    """
    Обрабатывает поиск фильмов по ключевому слову в названии.
    Запрашивает у пользователя строку, выводит результаты постранично
    по PAGE_SIZE штук и сохраняет запрос в MongoDB.

    :return: None.
    """
    keyword = input('Введите ключевое слово для поиска по названию: ').strip()
    if not keyword:
        print('Поисковый запрос не может быть пустым.')
        return

    mongo_client.save_query('by_keyword', {'keyword': keyword})

    offset = 0
    while True:
        films = mysql_client.fetch_films_by_title(keyword, PAGE_SIZE, offset)
        print_films(films, offset)

        if len(films) <= PAGE_SIZE:
            print('Это все результаты.')
            break

        if not ask_for_next_page():
            break
        offset += PAGE_SIZE


# ─────────────────────────────────────────
#  Поиск по жанру и диапазону годов
# ─────────────────────────────────────────

@logger.logger_decorator
def handle_search_movies_by_genre() -> None:
    """
    Обрабатывает поиск фильмов по жанру и диапазону годов выпуска.
    Перед вводом показывает пользователю список жанров и допустимый
    диапазон годов. Результаты выводятся постранично по PAGE_SIZE штук.
    Запрос сохраняется в MongoDB.

    :return: None.
    """
    genres = mysql_client.fetch_all_genres()
    if not genres:
        print('Не удалось загрузить жанры.')
        return

    print('\nДоступные жанры:')
    genre_map = {}
    for g in genres:
        print(f"  {g['category_id']}. {g['name']}")
        genre_map[str(g['category_id'])] = g

    year_range = mysql_client.fetch_year_range()
    min_year = year_range['min_year']
    max_year = year_range['max_year']
    print(f'\nГоды выпуска фильмов в базе: от {min_year} до {max_year}')

    genre_id_input = input('\nВведите номер жанра: ').strip()
    if genre_id_input not in genre_map:
        print('Неверный номер жанра.')
        return
    selected_genre = genre_map[genre_id_input]

    try:
        year_from_input = input(f'Год от ({min_year}–{max_year}): ').strip()
        year_from = int(year_from_input) if year_from_input else min_year

        year_to_input = input(f'Год до ({min_year}–{max_year}): ').strip()
        year_to = int(year_to_input) if year_to_input else max_year
    except ValueError:
        print('Неверный формат года.')
        return

    if not (min_year <= year_from <= max_year and min_year <= year_to <= max_year):
        print(f'Год должен быть в диапазоне {min_year}–{max_year}.')
        return

    if year_from > year_to:
        year_from, year_to = year_to, year_from

    mongo_client.save_query('by_genre_and_year', {
        'genre_id': selected_genre['category_id'],
        'genre_name': selected_genre['name'],
        'year_from': year_from,
        'year_to': year_to,
    })

    print(f'\nФильмы жанра «{selected_genre["name"]}» ({year_from}–{year_to}):\n')

    offset = 0
    while True:
        films = mysql_client.fetch_films_by_genre_and_year(
            selected_genre['category_id'], year_from, year_to, PAGE_SIZE, offset
        )
        print_films(films, offset)

        if len(films) <= PAGE_SIZE:
            print('Это все результаты.')
            break

        if not ask_for_next_page():
            break
        offset += PAGE_SIZE


# ─────────────────────────────────────────
#  Популярные запросы
# ─────────────────────────────────────────

def _format_query_doc(doc: dict, show_count: bool = False) -> str:
    """
    Форматирует документ из MongoDB в читаемую строку для отображения.

    :param doc: словарь с полями _id (type + params), count, last_used.
    :param show_count: если True — показывает количество повторений,
                       если False — показывает дату последнего использования.
    :return: отформатированная строка с описанием запроса.
    """
    query_type = doc['_id']['type']
    params = doc['_id']['params']

    if query_type == 'by_keyword':
        label = f"По ключевому слову: «{params.get('keyword', '?')}»"
    elif query_type == 'by_genre_and_year':
        label = (
            f"По жанру «{params.get('genre_name', '?')}» "
            f"({params.get('year_from', '?')}–{params.get('year_to', '?')})"
        )
    else:
        label = f"{query_type}: {params}"

    suffix = f"  — {doc['count']} раз(а)" if show_count else f"  — {doc['last_used'].strftime('%d.%m.%Y %H:%M')}"
    return label + suffix


@logger.logger_decorator
def handle_popular_queries_by_date() -> None:
    """
    Выводит 5 последних уникальных поисковых запросов, отсортированных по дате.

    :return: None.
    """
    results = mongo_client.fetch_popular_by_date(limit=5)
    if not results:
        print('История запросов пуста.')
        return
    print('\nПоследние 5 уникальных запросов:\n')
    for i, doc in enumerate(results, 1):
        print(f'  {i}. {_format_query_doc(doc, show_count=False)}')
    print()


@logger.logger_decorator
def handle_popular_queries_by_number() -> None:
    """
    Выводит топ-5 поисковых запросов, отсортированных по частоте использования.

    :return: None.
    """
    results = mongo_client.fetch_popular_by_frequency(limit=5)
    if not results:
        print('История запросов пуста.')
        return
    print('\nТоп-5 запросов по частоте:\n')
    for i, doc in enumerate(results, 1):
        print(f'  {i}. {_format_query_doc(doc, show_count=True)}')
    print()


# ─────────────────────────────────────────
#  Конфигурация меню
# ─────────────────────────────────────────

menu_config = {
    'title': 'Главное меню',
    'items': {
        '1': {
            'text': 'Поиск фильмов',
            'submenu': {
                'title': 'Меню поиска фильмов',
                'items': {
                    '1': {'text': 'Поиск по ключевому слову', 'action': handle_search_movies_by_keyword},
                    '2': {'text': 'Поиск по жанру и годам', 'action': handle_search_movies_by_genre},
                    '0': {'text': 'Назад', 'action': 'back'},
                },
            },
        },
        '2': {
            'text': 'Популярные запросы',
            'submenu': {
                'title': 'Меню популярных запросов',
                'items': {
                    '1': {'text': 'По дате (последние)', 'action': handle_popular_queries_by_date},
                    '2': {'text': 'По частоте', 'action': handle_popular_queries_by_number},
                    '0': {'text': 'Назад', 'action': 'back'},
                },
            },
        },
        '0': {
            'text': 'Выход',
            'action': lambda: sys.exit(0),
        },
    },
}


# ─────────────────────────────────────────
#  Движок меню
# ─────────────────────────────────────────

def run_menu(config: dict) -> None:
    """
    Запускает интерактивный цикл консольного меню.
    Поддерживает вложенные подменю через стек и действие 'back' для возврата.

    :param config: словарь конфигурации меню с полями title и items.
    :return: None.
    """
    stack = [config]

    while stack:
        current_menu = stack[-1]
        print(f'\n=== {current_menu.get("title", "Меню")} ===')

        for key, value in current_menu['items'].items():
            print(f'  {key}: {value["text"]}')

        choice = input('\nВыберите пункт меню: ').strip()

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
                    print(f'Ошибка: {e}')
        else:
            print('Неверный ввод. Повторите ещё раз.')