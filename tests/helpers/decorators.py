import pathlib
import inspect

from termx.fmt import Format, style


def need_to_do(func):
    """
    Utility to Cleanly Remind us to Complete a Test Placeholder
    """
    def wrapped(instance, *args, **kwargs):
        fmt = Format(styles=['bold'], color='red')
        print(f"{fmt('Need to Do')}: {Format(color='blue')(func.__name__)}")
        return func(instance, *args, **kwargs)
    return wrapped


def need_to_fix(reason):
    """
    Utility to Cleanly Remind us to Fix a Test
    """
    def decorator(func):
        def wrapped(instance, *args, **kwargs):
            fmt = Format(styles=['bold'], color='red')
            print(
                f"{fmt('Need to Fix')}: {Format(color='blue')(func.__name__)} "
                f"(Reason: {style('bold')(reason)})"
            )
        return wrapped
    return decorator


def is_numeric(val):
    try:
        int(val)
    except ValueError:
        return False
    else:
        return True


def allow_string_path(func):

    def decorated_method(instance, *args, **kwargs):

        path = args[0]

        if not isinstance(path, pathlib.Path):
            path = pathlib.PosixPath(path)

        if len(args) != 1:
            a = (path, ) + args[1:]
            return func(instance, *a, **kwargs)
        return func(instance, path, **kwargs)

    def decorated(*args, **kwargs):

        path = args[0]

        if not isinstance(path, pathlib.Path):
            path = pathlib.PosixPath(path)

        if len(args) != 1:
            a = (path, ) + args[1:]
            return func(*a, **kwargs)
        return func(path, **kwargs)

    # Not sure why, but `inspect.ismethod(func)` does not seem to return True
    # for the methods we are decorating but returns False for both method and
    # general functions.
    func_params = inspect.signature(func).parameters
    if 'self' in func_params or 'cls' in func_params:
        return decorated_method
    return decorated


def no_absolute_path(func):

    def check_path(*args):
        path = args[0]

        if not isinstance(path, pathlib.Path):
            path = pathlib.PosixPath(path)

        if path.is_absolute():
            raise ValueError('Path cannot be absolute.')

        return path

    def decorated_method(instance, *args, **kwargs):
        path = check_path(*args)

        if len(args) != 1:
            a = (path, ) + args[1:]
            return func(instance, *a, **kwargs)
        return func(instance, path, **kwargs)

    def decorated(*args, **kwargs):
        path = check_path(*args)

        if len(args) != 1:
            a = (path, ) + args[1:]
            return func(*a, **kwargs)
        return func(path, **kwargs)

    # Not sure why, but `inspect.ismethod(func)` does not seem to return True
    # for the methods we are decorating but returns False for both method and
    # general functions.
    func_params = inspect.signature(func).parameters
    if 'self' in func_params or 'cls' in func_params:
        return decorated_method
    return decorated


def require_absolute_path(func):

    def check_path(*args):
        path = args[0]

        if not isinstance(path, pathlib.Path):
            path = pathlib.PosixPath(path)

        if not path.is_absolute():
            raise ValueError('Path must be absolute.')

        return path

    def decorated_method(instance, *args, **kwargs):
        path = check_path(*args)

        if len(args) != 1:
            a = (path, ) + args[1:]
            return func(instance, *a, **kwargs)
        return func(instance, path, **kwargs)

    def decorated(*args, **kwargs):
        path = check_path(*args)

        if len(args) != 1:
            a = (path, ) + args[1:]
            return func(*a, **kwargs)
        return func(path, **kwargs)

    # Not sure why, but `inspect.ismethod(func)` does not seem to return True
    # for the methods we are decorating but returns False for both method and
    # general functions.
    func_params = inspect.signature(func).parameters
    if 'self' in func_params or 'cls' in func_params:
        return decorated_method
    return decorated
