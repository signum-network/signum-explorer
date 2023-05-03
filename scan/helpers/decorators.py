from functools import wraps
from django.core.cache import cache

def lock_decorator(key=None, expire=None, ident=None, auto_renewal=False):
    def decorator(func):
        def _make_lock_key():
            return f"lock_decorator:{key or func.__name__}"

        @wraps(func)
        def inner(*args, **kwargs):
            lock_key = _make_lock_key()
            with cache.lock(lock_key, expire, ident, auto_renewal):
                return func(*args, **kwargs)

        return inner
    return decorator

def skip_if_running(f):
    task_name = f'{f.__module__}.{f.__name__}'

    @wraps(f)
    def wrapped(self, *args, **kwargs):
        workers = self.app.control.inspect().active()

        if workers is None: return None

        for worker, tasks in workers.items():
            for task in tasks:
                if (task_name == task['name'] and
                        tuple(args) == tuple(task['args']) and
                        kwargs == task['kwargs'] and
                        self.request.id != task['id']):
                    print(f"Task {task_name}[{task['id']}] is already running on {worker}")

                    return None

        return f(self, *args, **kwargs)

    return wrapped