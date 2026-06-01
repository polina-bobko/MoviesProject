class DBConnectionError(Exception):
    """Raised when a MySQL database connection cannot be established."""
    pass


class MongoConnectionError(Exception):
    """Raised when a MongoDB connection cannot be established."""
    pass


class QueryError(Exception):
    """Raised when a database query fails."""
    pass