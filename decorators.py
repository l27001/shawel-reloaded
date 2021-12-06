from functools import wraps
from methods import Methods

def dostup1_needed(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if(args[0]['dostup'] < 1):
            return Methods.send(args[0]['chat_id'], "⛔ У вас нет прав на использование этой команды.")
        return f(*args, **kwargs)
    return decorated_function

def dostup2_needed(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if(args[0]['dostup'] < 2):
            return Methods.send(args[0]['chat_id'], "⛔ У вас нет прав на использование этой команды.")
        return f(*args, **kwargs)
    return decorated_function