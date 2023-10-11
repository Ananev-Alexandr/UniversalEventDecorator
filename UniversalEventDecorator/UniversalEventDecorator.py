import asyncio
import functools
import time
import gc

from UniversalEventDecorator.UniversalLogger import UniversalLogger


has_fastapi = False
has_torch = False

try:
    from fastapi import HTTPException
    has_fastapi = True
except ImportError:
    print("Warning: fastapi is not available")

try:
    import torch
    has_torch = True
except ImportError:
    print("Warning: torch is not available")


class UniversalEventDecorator(UniversalLogger):

    def __call__(self, func):
        function_name = func.__name__ if hasattr(func, '__name__') else repr(func)

        # Обертка для асинхронных функций
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.perf_counter()

                try:
                    result = await func(*args, **kwargs)
                    self._logger_report(function_name, start_time)
                    return result
                except Exception as e:
                    return self._handle_exception(e, function_name)
                finally:
                    if has_torch:
                        gc.collect()
                        torch.cuda.empty_cache()

            return async_wrapper

        # Обертка для синхронных функций
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.perf_counter()

                try:
                    result = func(*args, **kwargs)
                    self._logger_report(function_name, start_time)
                    return result
                except Exception as e:
                    return self._handle_exception(e, function_name)
                finally:
                    if has_torch:
                        gc.collect()
                        torch.cuda.empty_cache()

            return sync_wrapper

    # Очистка памяти после выполнения функции
    def _final_cleanup(self):
        if has_torch:
            gc.collect()
            torch.cuda.empty_cache()

    # Обработка исключений
    def _handle_exception(self, e, function_name):
        self._handle_error(e, function_name)
        if has_fastapi:
            raise HTTPException(
                status_code=500,
                detail=e.__str__()
            )
        else:
            return {
                "status_code": 500,
                "message": e.__str__()
            }


universal_event_decorator = UniversalEventDecorator()
logger = universal_event_decorator.logger
