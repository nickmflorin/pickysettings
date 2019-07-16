import contextlib
import os
import pathlib
import pytest
import sys

from pickysettings.core.exceptions import SettingsLoadError
from .helpers import FileContent, module, no_absolute_path


@pytest.fixture
def module_string():
    return module._get_module_string


@pytest.fixture
def mock_cwd(monkeypatch, tmpdir):
    def create_mock():
        def mocker():
            return str(tmpdir)
        monkeypatch.setattr(os, 'getcwd', mocker)
    return create_mock


@pytest.fixture
def raises_load_error():

    @contextlib.contextmanager
    def _raises_load_error(err):
        try:
            with pytest.raises(SettingsLoadError) as exc:
                yield exc
        finally:
            assert [e.exc.__class__ for e in exc.value.errors] == [err]
    return _raises_load_error


@pytest.fixture(scope='class')
def file_client(request):
    """
    [x] TODO:
    --------
    Get to work for non test class cases, if at all applicable.
    """

    def _generate_random_content(cls, *args, **kwargs):
        num_params = kwargs.pop('num_params', 2)
        file_content = FileContent(*args, **kwargs)
        file_content.randomize(test_cls=request.cls, num_params=num_params)
        return file_content

    request.cls.file_count = 0

    request.cls.file_content = FileContent
    request.cls.randomize_content = _generate_random_content

    yield

    request.cls.file_count = 0


@pytest.fixture
def tmp_module(tmpdir, mock_cwd):
    """
    Factory for creating a temporary module at the given path.  If the path
    references a file, the file will also be created inside the module.

    [!] IMPORTANT:
    -------------
    We must always ensure that `tmpdir` is in the `sys.path` so that
    we can directly import modules nested inside of the non-module tmpdir
    structure.

    We must also always ensure that we mock os.getcwd() to point to tmpdir so
    that all instances of LazySettings look in tmpdir for the absolute paths.
    """
    mock_cwd()
    sys.path.insert(0, str(tmpdir))

    @no_absolute_path
    def _create_temp_module(path, content=None, invalid=False):

        tmp_path = pathlib.PosixPath(tmpdir)
        try:
            path = path.relative_to(tmp_path)
        except ValueError:
            pass

        sys.path.insert(0, str(tmpdir))
        mod = module(tmpdir, path, content=content, invalid=invalid)

        created = mod.create()
        mod.reload()
        return created

    return _create_temp_module
