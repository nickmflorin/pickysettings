import os
import importlib
import pathlib
import pytest
import textwrap


TMP_MODULE = 'tests/tmp_modules'


def get_tests_path():
    return pathlib.PosixPath(TMP_MODULE)


def get_tests_absolute_path():

    tests_dir = get_tests_path()
    if not tests_dir.exists():
        raise RuntimeError('There must be a temporary module directory at %s.'
            % tests_dir.as_posix())
    return tests_dir.absolute()


def get_path_for_tests(path, directory=False):
    """
    For a given path, returns the path inside of the tests module
    directory.

    >>> get_path_for_tests('app/settings/dev.py')
    >>> 'tests/tmp_modules/app/settings/dev.py'
    """
    if not isinstance(path, pathlib.Path):
        path = pathlib.PosixPath(path)

    tests_path = get_tests_path()

    if len(path.parts) == 2:
        if path.parts[0] == tests_path.parts[0] and path.parts[1] == tests_path.parts[1]:
            raise RuntimeError('Path %s is already in tests directory.' % path)

    path = tests_path.joinpath(path)
    if directory and path.suffix:
        return path.parent
    return path


def get_absolute_path_for_tests(path, directory=False):
    if path.is_absolute():
        if not directory and path.suffix:
            return path.parent
        return path
    path = get_path_for_tests(path, directory=directory)
    return path.absolute()


def get_module_path_for_tests(path, directory=False):
    """
    For a given path, returns the module path inside of the tests module
    directory.

    >>> get_module_path_for_tests('app/settings/dev.py')
    >>> 'tests.tmp_modules.app.settings.dev'
    """
    if not isinstance(path, pathlib.Path):
        path = pathlib.PosixPath(path)

    path = get_absolute_path_for_tests(path)
    tests_path = get_tests_absolute_path()

    path = path.relative_to(tests_path)

    if directory and path.suffix:
        path = path.parent
    else:
        path = path.with_suffix('')
    return '.'.join(path.parts)


# @pytest.fixture
# def get_test_relative_abs_path(get_tests_path, tests_absolute_path):

#     def _get_test_relative_path(path):
#         if not isinstance(path, pathlib.Path):
#             path = pathlib.PosixPath(path)

#         if path.is_absolute():
#             return path.relative_to(tests_absolute_path)
#         else:
#             path = get_tests_path(path)
#             return path.absolute()

#     return _get_test_relative_path


@pytest.fixture
def mock_cwd(monkeypatch, tmpdir):
    def create_mock():
        def mocker():
            return str(tmpdir)
        monkeypatch.setattr(os, 'getcwd', mocker)
    return create_mock


@pytest.fixture(scope="function")
def create_temp_dir(tmpdir):
    def create_dir(*args):
        path = args[-1]

        parts = pathlib.Path(path).parts
        parts = [pt for pt in parts if pt != '/']

        tmp = tmpdir
        for pt in parts:
            tmp = tmp.join(pt)
            if tmp.exists():
                continue
            tmp.mkdir()
        return tmp
    return create_dir


@pytest.fixture(scope="function")
def create_temp_file(tmpdir):
    def create_file(*args, directory=None, content=None):
        file = args[-1]

        path = tmpdir
        if directory:
            path = tmpdir.join(pathlib.PosixPath(directory))
            if not path.exists():
                raise RuntimeError(
                    "Cannot create test file in directory until temp directory "
                    "created."
                )

        p = path / file
        if content:
            p.write(content)
        else:
            p.write('empty')
        return p

    return create_file


# @pytest.fixture(scope='function')
# def reload_tmp_modules(TMP_MODULE_DIR):
#     """
#     When we update or add modules to the tmp_modules directory, we have to
#     reload the tmp_modules module, otherwise the updates will not be reflected
#     in LazySettings and new settings files added will raise import errors.

#     [x] TODO:
#     ---------
#     This does not work for updating the contents of an imported module file
#     in the same test.  If we use multiple module files in the same test, we
#     need to create two separate files instead of updating the content of the first
#     file.

#     [x] NOTE:
#     ---------
#     Ideally, we would want to test invalid imports in modules, but that raises
#     errors in this fixture - there has to be a more clever way of doing this.

#     If we do the following:

#     >>> try:
#     >>>     importlib.import_module(module_path)
#     >>> except ModuleNotFoundError:
#     >>>     pass

#     we run the risk of suppressing unintentional issues in the modules we are
#     creating.
#     """
#     modules = []

#     def _reload_tmp_modules(*parts, invalid=False):
#         """
#         Parts are specified relative to tests/tmp_modules.

#         The `invalid` keyword argument indicates that we are expecting the
#         given module file to cause an error during import and want this error
#         to be raised in the actual code, not during the reloading of the
#         module in tests.

#         [!] IMPORTANT:
#         --------------
#         If the `invalid` keyword argument is specified, and the module path
#         indicated by `parts` does not point to that specific file, but rather
#         a containing module, we run the risk of not reloading other parts of
#         the containing module.
#         """
#         import importlib

#         module_parts = TMP_MODULE_DIR.split('/') + list(parts)
#         module_path = '.'.join(module_parts)

#         try:
#             module = importlib.import_module(module_path)
#         except ImportError as e:
#             if invalid:
#                 print('Intentionally Ignoring Invalid Module')
#                 return
#             raise e
#         else:
#             if module not in modules:
#                 modules.append(module)
#             else:
#                 importlib.reload(module)

#             # print('Reloading Module %s' % module_path)
#             # try:
#             #     importlib.reload(module)
#             # except Exception as e:
#             #     import ipdb; ipdb.set_trace()

#             #     if invalid:
#             #         print('Warning: Should not be here.')
#             #         return
#             #     raise e

#     return _reload_tmp_modules


@pytest.fixture
def write_file_content():

    def _create_variable_content(**kwargs):
        lines = []
        for key, val in kwargs.items():
            line_val = "%s = '%s'" % (key, val)
            lines.append(line_val)
        return "\n".join(lines)

    def _write(file, content):
        if isinstance(content, dict):
            content = _create_variable_content(**content)
        else:
            content = textwrap.dedent(content)
        file.write_text(content)

    return _write


@pytest.fixture
def temp_module(write_file_content):
    """
    Fixture that returns a context manager that allows us to temporarily create
    and remove a settings file in a module in the `tests/tmp` directory.

    When testing settings that are read, they are loaded with importlib, so the
    settings module file must be in a module in the pickysettings root.  This would
    be difficult to do using the tmpdir, since it goes several layers deep.

    Instead, we create temporary modules inside of `tests/tmp_modules` that are
    created and destroyed for each test.

    [!] IMPORTANT
    -------------
    Current Working Directory Cannot be Mocked

    [!] IMPORTANT
    -------------
    Reloading Modules

    If we update the content of a settings file after initially creating it in
    the same test, it will not be reloaded correctly and the new values will
    not update.

        >>> temp_module('app/settings/dev.py', content={'VALUE': 1})
        >>> settings = test_settings('dev', base_dir='app/settings')
        >>> settings.VALUE
        >>> 1

        >>> temp_module('app/settings/dev.py', content={'VALUE': 2})
        >>> settings = test_settings('dev', base_dir='app/settings')
        >>> settings.VALUE
        >>> 1

    If we want to run additional logic with altered content in the same test,
    we have to create another temporary module file:

        >>> temp_module('app/settings/dev2.py', content={'VALUE': 2})
    """

    def _reload_module_file(path, invalid=False):

        module_path = get_module_path_for_tests(path)
        print('Reloading %s' % module_path)

        module = importlib.import_module(module_path)
        importlib.reload(module)

    def _instantiate_module(path):
        """
        Creates a module at the given path by creating a directory with a name
        corresponding to the last part of the path (if it does not already exist)
        and including an __init__.py file in the created directory.
        """

        # Create Folder for Module if it Does Not Exist
        if not path.exists():
            path.mkdir()

        # Create Init File for Module
        init_file = path.joinpath('__init__.py')
        if not init_file.exists():
            init_file.touch()

    def _instantiate_module_file(path, content=None):
        """
        Creates a file at the given path assuming that the containing directory
        already exists and is a module.

        If content is provided, it can either be a string or a dict.  If it is
        a dict, a series of key-value Python variables are created.  The content
        is then written to the file.
        """
        PATH_EXISTS = False

        if path.exists():
            PATH_EXISTS = True
            path.unlink()

        path.touch()
        if content:
            write_file_content(path, content)

        if PATH_EXISTS:
            _reload_module_file(path)

    def _create_temp_module(path, content=None, invalid=False):
        """
        Creates a temporary module at the given path.  If the path references
        a file, and `content` is specified, will write the content to the file.

        If the path references a file and content is specified, and `invalid`
        is True, we are expecting that the module file will be invalid which
        will result in an error during import, which we want to be raised in
        the code we are testing, instead of the test code importing the module.
        """
        if not isinstance(path, pathlib.Path):
            path = pathlib.PosixPath(path)

        if path.is_absolute():
            raise RuntimeError('Path to settings module cannot be absolute.')

        if path.suffix:
            if path.suffix != '.py':
                raise RuntimeError('Path must point to valid Python file.')

        module_path = get_absolute_path_for_tests(path, directory=True)
        _instantiate_module(module_path)

        if path.suffix:
            module_path = get_absolute_path_for_tests(path)
            print('Creating Module File %s' % module_path)
            _instantiate_module_file(module_path, content=content)

        return module_path

    return _create_temp_module


@pytest.fixture
def remove_temp_module():
    """
    Removes the tests/tmp directory used to store the settings modules.

    [!] IMPORTANT
    -------------
    Current Working Directory Cannot be Mocked
    """
    def _remove_module(path):
        if not isinstance(path, pathlib.Path):
            path = pathlib.PosixPath(path)

        if path.suffix:
            raise RuntimeError('Path to settings module must not point to a file.')

        for child in path.iterdir():
            if child.is_dir():
                _remove_module(child)
            else:
                child.unlink()

    def _remove_temp_module():
        tmp_path = pathlib.PosixPath(TMP_MODULE)
        tmp_path = tmp_path.absolute()
        _remove_module(tmp_path)

    return _remove_temp_module


@pytest.fixture(scope="function")
def test_settings():
    """
    Creates an instance of LazySettings with the base directory adjusted for
    the temporary settings module.
    """
    def _test_settings(*args, base_dir=None, **kwargs):

        from pickysettings import LazySettings

        settings = list(args) or []
        if settings:
            if hasattr(args[0], '__name__'):
                settings = list(args)[1:]

        base = pathlib.PosixPath(TMP_MODULE)
        if base_dir:
            base = base.joinpath(base_dir)

        obj = LazySettings(*settings, base_dir=base, **kwargs)
        return obj

    return _test_settings
