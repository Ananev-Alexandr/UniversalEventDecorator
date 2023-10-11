import asyncio
import functools
import logging
import colorlog
import time
import traceback


import_flag = False

try:
    from fastapi import HTTPException
    import_flag = True
except Exception:
    pass


class UniversalEventDecorator:
    formatter = colorlog.ColoredFormatter(
        "%(log_color)s%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        }
    )

    def __init__(self):
        # Создание логгера и установка уровня логирования
        self.logger = colorlog.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Потоковый обработчик, который выводит логи на консоль
        stream_handler = colorlog.StreamHandler()
        stream_handler.setFormatter(self.formatter)
        self.logger.addHandler(stream_handler)

    def _logger_report(self, function_name, start_time):
        """Создает отчет об успешном выполнении функции."""
        execution_time = time.perf_counter() - start_time  # secs
        self.logger.info(f"Функция {function_name} отработала успешно за {execution_time:.2f} секунд.")

    def __call__(self, func):
        function_name = func.__name__ if hasattr(func, '__name__') else repr(func)

        # Проверка, является ли функция асинхронной
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.perf_counter()

                try:
                    result = await func(*args, **kwargs)
                    self._logger_report(function_name, start_time)
                    return result
                except Exception as e:
                    self._handle_error(e, function_name)
                    if import_flag:
                        raise HTTPException(
                            status_code=500,
                            detail=e.__str__()
                        )
                    else:
                        return {
                            "status_code": 500,
                            "message": e.__str__()
                            }

            return async_wrapper

        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.perf_counter()

                try:
                    result = func(*args, **kwargs)
                    self._logger_report(function_name, start_time)
                    return result
                except Exception as e:
                    self._handle_error(e, function_name)
                    if import_flag:
                        raise HTTPException(
                            status_code=500,
                            detail=e.__str__()
                        )
                    else:
                        return {
                            "status_code": 500,
                            "message": e.__str__()
                            }

            return sync_wrapper

    def _handle_error(self, e, function_name):
        tb = traceback.format_exc()
        logger.error(f"Произошла ошибка в функции {function_name}: {e}\n{tb}")

        # Проверка, является ли исключение HTTP-исключением или имеет атрибут 'status_code'
        if hasattr(e, 'status_code') or type(e).__name__ == "HTTPException":
            raise e


universal_event_decorator = UniversalEventDecorator()
logger = universal_event_decorator.logger
