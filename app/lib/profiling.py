import functools
from collections import Sized

from timeit import default_timer as timer
from typing import Any, Callable


def timeit(method: Callable[..., Any]) -> Callable[..., Any]:
    """Профайлер времени выполнения функции."""

    @functools.wraps(method)
    async def _timeit(*args, **kwargs):
        ts = timer()
        result = await method(*args, **kwargs)
        te = timer()
        elapsed_time = (te - ts) * 1000

        log = f'Call: <{method.__name__}> | Elapsed time: {elapsed_time:.2f} ms'
        if isinstance(result, Sized):
            log = f'{log} | Type: {type(result)} | Len: {len(result)}'

        print(log)
        return result

    return _timeit
