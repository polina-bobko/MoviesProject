class DBConnectionError(Exception):
    """Ошибка подключения к базе данных"""
    pass


class MongoConnectionError(Exception):
    """Ошибка подключения к MongoDB"""
    pass


class QueryError(Exception):
    """Ошибка выполнения запроса"""
    pass