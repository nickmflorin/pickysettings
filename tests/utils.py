import pathlib
import textwrap
import importlib
import sys


TMP_MODULE = 'tests/tmp_modules'


def allow_string_path(func):
    def decorated(*args, **kwargs):
        path = args[0]
        if not isinstance(path, pathlib.Path):
            path = pathlib.PosixPath(path)

        if len(args) != 1:
            a = (path, ) + args[1:]
            return func(*a, **kwargs)
        return func(path, **kwargs)
    return decorated


def no_absolute_path(func):
    def decorated(*args, **kwargs):
        path = args[0]

        if not isinstance(path, pathlib.Path):
            path = pathlib.PosixPath(path)

        if path.is_absolute():
            raise ValueError('Path cannot be absolute.')

        if len(args) != 1:
            a = (path, ) + args[1:]
            return func(*a, **kwargs)
        return func(path, **kwargs)

    return decorated


def require_absolute_path(func):
    def decorated(*args, **kwargs):
        path = args[0]

        if not isinstance(path, pathlib.Path):
            path = pathlib.PosixPath(path)

        if not path.is_absolute():
            raise ValueError('Path must be absolute.')

        if len(args) != 1:
            a = (path, ) + args[1:]
            return func(*a, **kwargs)
        return func(path, **kwargs)

    return decorated


@allow_string_path
def starts_with_test_module(path):
    if len(path.parts) >= 2:
        if path.parts[0] == pathlib.PosixPath(TMP_MODULE).parts[0]:
            if path.parts[1] == pathlib.PosixPath(TMP_MODULE).parts[1]:
                return True
    return False


@allow_string_path
def append_to_test_module(path):
    if starts_with_test_module(path):
        raise ValueError('Path %s already appended to %s.' % (
            path.as_posix(), TMP_MODULE
        ))
    path = pathlib.PosixPath(TMP_MODULE).joinpath(path)
    return path


@allow_string_path
def separate_from_test_module(path):
    if not starts_with_test_module(path):
        raise ValueError('Path %s does not start with %s.' % (
            path.as_posix(), TMP_MODULE
        ))
    parts = path.parts[2:]
    return pathlib.PosixPath(*parts)


@allow_string_path
def safe_append_to_test_module(path):
    try:
        return append_to_test_module(path)
    except ValueError:
        return path


@allow_string_path
def safe_separate_from_test_module(path):
    try:
        return separate_from_test_module(path)
    except ValueError:
        return path


def get_tests_module_path(*args, absolute=False):
    """
    A utility that has functions in multiple different ways, depending on the
    value of `path`.

    (1) `path` is an absolute path

        Returns the path inside of the test modules directory.

            >>> get_tests_module_path('/repos/pickysettings/tests/tmp_modules/app/settings/dev.py')
            >>> 'tests/tmp_modules/app/settings/dev.py'

    (2) `path` is not provided

        Returns the path of the base tests module directory.

            >>> get_tests_module_path()
            >>> 'tests/tmp_modules'

        If `absolute` is specified, returns the absolute path of the base tests
        module directory.

            >>> get_tests_module_path(absolute=True)
            >>> '/repos/pickysettings/tests/tmp_modules'

    (3) `path` is non-absolute path

        Returns the non-absolute path of the provided path inside of the tests
        module directory.

            >>> get_tests_module_path('app/settings')
            >>> 'tests/tmp_modules/app/settings'

        If `absolute` is specified, returns the absolute path of the provided path
        inside of the tests module directory.

            >>> get_tests_module_path('app/settings', absolute=True)
            >>> '/repos/pickysettings/tests/tmp_modules/app/settings'
    """

    path = None
    if len(args) == 1:
        path = args[0]

    if not path:
        path = pathlib.PosixPath(TMP_MODULE)
        if absolute:
            return path.absolute()
        return path

    if not isinstance(path, pathlib.Path):
        path = pathlib.PosixPath(path)

    # If given an absolute path, return path relative to the tests
    # module.
    if path.is_absolute():
        abs_test_path = get_tests_module_path(absolute=True)
        rel_path = path.relative_to(abs_test_path)
        return append_to_test_module(rel_path)

    else:
        path = safe_append_to_test_module(path)
        if absolute:
            return path.absolute()
        return path


def write_file_content(file, content):

    def _is_numeric(val):
        try:
            int(val)
        except ValueError:
            return False
        else:
            return True

    def _create_variable_content(**kwargs):
        lines = []
        for key, val in kwargs.items():
            if not _is_numeric(val):
                line_val = "%s = '%s'" % (key, val)
            else:
                line_val = "%s = %s" % (key, val)
            lines.append(line_val)
        return "\n".join(lines)

    if isinstance(content, dict):
        content = _create_variable_content(**content)
    else:
        content = textwrap.dedent(content)

    file.write_text(content)


def get_module_string(path):
    """
    For a given path, returns the module path inside of the tests module
    directory.

    >>> module_string('app/settings/dev.py')
    >>> 'tests.tmp_modules.app.settings.dev'

    [x] NOTE:
    --------
    Will currently not work for absolute paths, which we might want to enforce
    that it can work for.
    """
    if not isinstance(path, pathlib.Path):
        path = pathlib.PosixPath(path)

    if path.is_absolute():
        raise ValueError('Path cannot be absolute.')

    if path.suffix:
        path = path.with_suffix('')
    return '.'.join(path.parts)


def reload_module_file(path, invalid=False):
    """
    When we update or add modules to the tmp_modules directory, we have to
    reload the tmp_modules module, otherwise the updates will not be reflected
    in LazySettings and new settings files added will raise import errors.

    [x] NOTE:
    ---------
    Ideally, we would want to test invalid imports in modules, but that raises
    errors in this fixture - there has to be a more clever way of doing this.

    If we do the following:

    >>> try:
    >>>     importlib.import_module(module_path)
    >>> except ModuleNotFoundError:
    >>>     pass

    we run the risk of suppressing unintentional issues in the modules we are
    creating.
    """

    # NOTE:
    # I don't think we are currently using the `invalid` parameter anymore so
    # we can probably get rid of it.

    # Path Need to Start with "/tests/tmp_modules"
    path = safe_append_to_test_module(path)
    module_path = get_module_string(path)

    try:
        module = importlib.import_module(module_path)
    except ImportError as e:
        if invalid:
            print('Intentionally Not Reloading %s with Invalid Content' % module_path)
            return
        raise e
    else:
        print('Reloading %s' % module_path)
        importlib.reload(module)


@no_absolute_path
def instantiate_test_module(path, content=None, invalid=False):
    """
    Creates a module at the given path by looking at the module path relative
    to the tests directory for modules, iteratively creating modules for
    each part in the path moving downwards.

    Each module level is instantiated with a directory and an __init__.py
    file.  If the path indicates a file at the base, the file is created
    and instantiated with content.

    [!] IMPORTANT
    -------------
    Path cannot be absolute.
    """

    @require_absolute_path
    def create_module_dir(path, name):
        """
        At the given path, creates a module with the provided name by creating
        a directory if it does not exist and establishing an __init__.py file.
        """

        # Path Cannot Start with "/tests/tmp_modules"
        path = safe_separate_from_test_module(path)

        # Create Folder for Module if it Does Not Exist
        module_path = path.joinpath(name)
        if not module_path.exists():
            module_path.mkdir()

        # Create Init File for Module
        init_file = module_path.joinpath('__init__.py')
        if not init_file.exists():
            init_file.touch()

        return module_path

    @require_absolute_path
    def create_module_file(path, name, content=None, invalid=False):
        """
        Creates a file with the associated `name` (including suffix) at the
        module path `path`.  If `content` is specified, the content is written
        to the file.

        If the file already existed, we reload the module at this path so
        that any new content written to the file is reloaded.

        [!] IMPORTANT
        -------------
        Path must be absolute.
        """

        # Path Cannot Start with "/tests/tmp_modules"
        path = safe_separate_from_test_module(path)

        path = path.joinpath(name)
        if not path.exists():
            path.touch()

        if content:
            write_file_content(path, content)

        # Reloading the module file only if the file already existed does not
        # seem to be working, most likely due to removing modules between tests or
        # sibling modules/files not being reloaded.
        module_path = get_tests_module_path(path)
        module_str = get_module_string(module_path)

        importlib.invalidate_caches()

        if sys.modules.get(module_str):
            # Honestly not sure here if we have to reload all of the containing
            # modules as well...
            if not invalid:
                reload_module_file(module_path)
            else:
                # This will prevent us from having to reimport the module here,
                # since it will cause an error, but will force the actual settings
                # code to reload the module.
                del sys.modules[module_str]

        return module_path

    # Path Cannot Start with "/tests/tmp_modules"
    path = safe_separate_from_test_module(path)

    path_parts = path.parts
    if path.suffix:
        path_parts = path.parent.parts

    module_path = get_tests_module_path(absolute=True)
    for name in path_parts:
        module_path = create_module_dir(module_path, name)

    if path.suffix:
        return create_module_file(module_path, path.name, content=content, invalid=invalid)
    return module_path


def remove_test_modules():
    """
    Removes the children modules of the tests/tmp directory used to store the
    settings modules used for tests.

    [!] IMPORTANT
    -------------
    Current Working Directory Cannot be Mocked
    """
    def remove_modules(path):
        for child in path.iterdir():
            if child.is_file():
                child.unlink()
            else:
                remove_modules(child)
                child.rmdir()

    base_path = get_tests_module_path(absolute=True)

    for child in base_path.iterdir():
        if child.is_file():
            child.unlink()
        else:
            remove_modules(child)
