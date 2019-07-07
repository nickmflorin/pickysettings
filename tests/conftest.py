import os
import pathlib
import pytest
import textwrap

from pickysettings import LazySettings
from pickysettings.core.setting import Setting


TMP_MODULE_DIR = 'tests/tmp_modules'


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
def reload_tmp_modules():
    """
    When we update or add modules to the tmp_modules directory, we have to
    reload the tmp_modules module, otherwise the updates will not be reflected
    in LazySettings and new settings files added will raise import errors.

    [x] TODO:
    ---------
    This does not work for updating the contents of an imported module file
    in the same test.  If we use multiple module files in the same test, we
    need to create two separate files instead of updating the content of the first
    file.

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
    def _reload_tmp_modules(*parts, invalid=False):
        """
        Parts are specified relative to tests/tmp_modules.

        The `invalid` keyword argument indicates that we are expecting the
        given module file to cause an error during import and want this error
        to be raised in the actual code, not during the reloading of the
        module in tests.

        [!] IMPORTANT:
        --------------
        If the `invalid` keyword argument is specified, and the module path
        indicated by `parts` does not point to that specific file, but rather
        a containing module, we run the risk of not reloading other parts of
        the containing module.
        """
        import importlib

        module_parts = TMP_MODULE_DIR.split('/') + list(parts)
        module_path = '.'.join(module_parts)

        try:
            module = importlib.import_module(module_path)
        except ImportError as e:
            if invalid:
                print('Intentionally Ignoring Invalid Module')
                return
            raise e
        else:
            importlib.reload(module)

    return _reload_tmp_modules


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
def temp_module(reload_tmp_modules, write_file_content):
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

    tests_dir = pathlib.PosixPath(TMP_MODULE_DIR).absolute()
    if not tests_dir.exists():
        raise RuntimeError('There must be a temporary module directory at %s.'
            % tests_dir.as_posix())

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
        if not path.exists():
            path.touch()

        if content:
            write_file_content(path, content)

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

        parts = path.parts

        if path.suffix:
            if path.suffix != '.py':
                raise RuntimeError('Path must point to valid Python file.')
            parts = path.parts[:-1]

        module_dir = tests_dir
        for pt in parts:
            module_dir = module_dir.joinpath(pt)
            _instantiate_module(module_dir)

        if path.suffix:
            module_dir = module_dir.joinpath(path.name)
            _instantiate_module_file(module_dir, content=content)

        module_path = module_dir.relative_to(tests_dir)
        module_path = module_path.with_suffix('')

        # Have to Reload `tests/tmp_modules` Module
        # We might be able to just reload the top level module instead of the
        # module at the file level...
        reload_tmp_modules(*module_path.parts, invalid=invalid)
        return module_dir

    return _create_temp_module


def remove_module(path):
    """
    Given a path to a directory in tests/tmp, removes the module, it's contents
    and all of it's children.

    -- tests
    ---- tmp
    -------- settings
    ------------__init__.py.py
    ------------dev.py

    >>> remove_module('tests/tmp/settings')

    -- tests
    ---- tmp

    [!] IMPORTANT
    -------------
    Current Working Directory Cannot be Mocked
    """
    if not isinstance(path, pathlib.Path):
        path = pathlib.PosixPath(path)

    if path.suffix:
        raise RuntimeError('Path to settings module must not point to a file.')

    for child in path.iterdir():
        if child.is_dir():
            remove_module(child)
        else:
            child.unlink()
    path.rmdir()


def remove_temp_module():
    """
    Removes the tests/tmp directory used to store the settings modules.

    -- tests
    ---- tmp
    -------- settings
    ------------__init__.py.py
    ------------dev.py

    >>> remove_settings_module()

    -- tests

    [!] IMPORTANT
    -------------
    Current Working Directory Cannot be Mocked
    """
    tmp_path = pathlib.PosixPath(TMP_MODULE_DIR)
    tmp_path = tmp_path.absolute()
    remove_module(tmp_path)


@pytest.fixture
def test_settings():
    """
    Creates an instance of LazySettings with the base directory adjusted for
    the temporary settings module.
    """
    def _test_settings(*args, base_dir=None, **kwargs):

        settings = list(args) or []
        if settings:
            if hasattr(args[0], '__name__'):
                settings = list(args)[1:]

        base = pathlib.PosixPath(TMP_MODULE_DIR)
        if base_dir:
            base = base.joinpath(base_dir)

        obj = LazySettings(*settings, base_dir=base, **kwargs)
        return obj

    return _test_settings


@pytest.fixture
def test_setting():
    """
    Creates an instance of Setting with the base directory adjusted for
    the temporary settings module.
    """
    def _test_settings(*args, base_path=None):

        value = args[0]
        if hasattr(args[0], '__name__'):
            value = list(args)[1]

        base = pathlib.PosixPath(TMP_MODULE_DIR)
        base_path = base.joinpath(base_path)
        return Setting(value, base_path=base_path)

    return _test_settings


@pytest.fixture(scope='function')
def settings_tmp_client(request, tmpdir, mock_cwd, create_temp_dir, create_temp_file):

    mock_cwd()
    request.cls.tmpdir = tmpdir
    request.cls.create_temp_dir = create_temp_dir
    request.cls.create_temp_file = create_temp_file


@pytest.fixture(scope='function')
def settings_module_client(request, settings_module, test_settings):
    request.cls.settings_module = settings_module
    request.cls.test_settings = test_settings
