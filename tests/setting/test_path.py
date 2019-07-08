import pathlib
import pytest

from pickysettings.core.setting import Setting
from pickysettings.core.exceptions import setting as setting_exceptions


"""
Tests pertaining to the .get_path() method of individual Setting objects
that are stored for each setting provided to LazySettings.

"2 Component Problem"
--------------------
There is no string manipulation method to differentiate between a
filename with an extension and a 2-component module string:
    (1) filename.ext
    (2) settings.filename

To solve this problem, we first assume it is a module path and check
if the absolute path generated based on that assumption exists.  If it
does not, we treat as a file path.

For tests, this means the following:
    - For tests of the get_path() method, where the "2 Component Problem"
      is applicable, we have to supply the base_dir.

In general, this means the following:
    - A simple string (i.e. "filename") will be treated as a module path,
      and the suffix will be assumed (".py").

[x] NOTE:
--------
The overall logical outcome of the assumption does not change, since an
exception will be raised if the intention was to use a module path but
it does not exist, and we treat it as a file path (because the file path
will not exist).  The error will just not be as indicative.
"""


def test_module_path():
    """
    For cases of a simple string or a module path that does not have (2)
    components, the Setting object should always treat as a module
    path and return a path corresponding to the module indicated in the path.

    For module paths, the default extension is assumed to be .py.
    """
    setting = Setting('dev')
    path = setting.get_path()
    assert str(path) == 'dev.py'

    setting = Setting('app.settings.dev')
    path = setting.get_path()
    assert str(path) == 'app/settings/dev.py'


def test_path():
    setting = Setting('app/settings/dev.py')
    path = setting.get_path()
    assert str(path) == 'app/settings/dev.py'


def test_absolute_path():
    setting = Setting('/app/settings/dev.py')
    path = setting.get_path()
    assert str(path) == '/app/settings/dev.py'


def test_without_extension():
    """
    When specifying as a path, and not a module path, the file extension is
    required - otherwise, there is no way to tell if it is referring to a
    directory, or a file.

    However, if the path is something like "filename", it doesn't matter if
    it is treated as a module path or a file path.

    [x] NOTE:
    --------
    This is, for all intents and purposes, the same thing as testing if we
    include a path without a file.

    Note that this is for all intents and purposes the same thing as testing
    if we include a path without a file.
    """
    setting = Setting('app/settings/filename')
    with pytest.raises(setting_exceptions.SettingIsNotFilePath):
        setting.get_path()

    setting = Setting('dev')
    path = setting.get_path()
    assert str(path) == 'dev.py'


def test_filename_with_extension(create_temp_dir, create_temp_file):
    """
    The file does not need to exist for .get_path(), but in some cases the
    directory does, since base_path will be checked.
    """
    base_path = pathlib.PosixPath('app/settings')
    setting = Setting('dev.py', base_path=base_path)
    path = setting.get_path()

    assert str(path) == 'dev.py'

    # Having the file there doesn't really make a difference because it
    # will always treat as a file with extension unless the module path exists.
    create_temp_dir('app/settings')
    create_temp_file('dev.py', directory='app/settings')

    setting = Setting('dev.py', base_path=base_path)
    path = setting.get_path()
    assert str(path) == 'dev.py'


def test_invalid_setting():

    setting = Setting('filename.')
    with pytest.raises(setting_exceptions.InvalidSetting):
        setting.get_path()

    # Folders cannot have "." in them, at least not right now.
    setting = Setting('app/settings.dev/dev.py')
    with pytest.raises(setting_exceptions.InvalidSetting):
        setting.get_path()

    setting = Setting('/prod.dev.py')
    with pytest.raises(setting_exceptions.InvalidSetting):
        setting.get_path()

    setting = Setting('.gitignore')
    with pytest.raises(setting_exceptions.UnsupportedFileType):
        setting.get_path()


def test_treats_as_module_path(create_temp_dir, create_temp_file):
    """
    When the "2 Component Problem" is applicable, if the file associated
    with a module path exists, the setting should be treated as a module
    path.

    If the file assocaited with the module path does not exist, the setting
    will be treated as a file, even if the file is invalid.  An exception
    will be raised downstream, in the get_absolute_path() method.
    """
    create_temp_dir('app/settings/deploy')
    create_temp_file('prod.py', directory='app/settings/deploy')

    base_path = pathlib.PosixPath('app/settings')

    setting = Setting('deploy.prod', base_path=base_path)
    path = setting.get_path()
    assert str(path) == 'deploy/prod.py'

    setting = Setting('deploy.debug', base_path=base_path)
    path = setting.get_path()
    assert str(path) == 'deploy.debug'
