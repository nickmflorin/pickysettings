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
