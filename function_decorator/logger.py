from typing import Callable
import datetime


def with_logger(func: Callable):
    def f():
        print('%s: running %s' % (str(datetime.datetime.now()), func.__name__))
        result = func()
        print('result:', result)
    return f
