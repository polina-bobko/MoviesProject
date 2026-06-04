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
        logger.info(f'Вызов функции: {func.__name__}')
        try:
            result = func(*args, **kwargs)
            logger.info(f'Функция {func.__name__} выполнена успешно')
            return result
        except Exception as e:
            logger.error(f'Ошибка в функции {func.__name__}: {e}')
            raise e

    return wrapper