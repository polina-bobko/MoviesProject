import logging
import functools

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
    ]
)
logger = logging.getLogger(__name__)

def logger_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f'Call the function: {func.__name__}')
        try:
            result = func(*args, **kwargs)
            logger.info(f'Function {func.__name__} successfully called.')
            return result
        except Exception as e:
            logger.error(f'Error in function {func.__name__}: {e}')
            raise e

    return wrapper