import os
import pathlib
import pytest

from pickysettings import LazySettings
from .utils import (
    instantiate_test_module, get_tests_module_path, starts_with_test_module,
    remove_test_modules, get_module_string)


@pytest.fixture
def tests_module_path():
    return get_tests_module_path()


@pytest.fixture
def tests_absolute_module_path():
    return get_tests_module_path(absolute=True)


@pytest.fixture
def module_string():
    return get_module_string


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


@pytest.fixture
def temp_module(tests_module_path):
    """
    Creates a temporary module at the given relative path inside of
    'tests/tmp_modules'.

    For instance, temp_module('app/settings/dev.py') will create the following
    structure:

    -- tests
    -- __init__.py
    ---- tmp_modules
    ---- __init__.py
    ------ app
    -------- __init__.py
    -------- settings
    ---------- __init__.py
    ---------- dev.py

    The fixture is in the test function scope.  When the function completes,
    all of the created test modules will be removed.

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
            raise ValueError('Path cannot be absolute.')

        # Path Cannot Start with "/tests/tmp_modules"
        if starts_with_test_module(path):
            raise ValueError('Path %s cannot start with %s.' % (tests_module_path, path))

        if path.suffix:
            if path.suffix != '.py':
                raise ValueError('Path must point to valid Python file.')

        module_path = instantiate_test_module(path, content=content, invalid=invalid)
        return module_path

    yield _create_temp_module
    remove_test_modules()


@pytest.fixture(scope="function")
def test_settings(tests_module_path):
    """
    Creates an instance of LazySettings with the base directory adjusted for
    the temporary settings module.
    """
    def _test_settings(*args, base_dir=None, **kwargs):
        settings = list(args) or []
        if settings:
            if hasattr(args[0], '__name__'):
                settings = list(args)[1:]

        base = tests_module_path
        if base_dir:
            base = base.joinpath(base_dir)

        obj = LazySettings(*settings, base_dir=base, **kwargs)
        return obj

    return _test_settings
