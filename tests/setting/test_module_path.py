import pathlib
import pytest

from pickysettings.core.setting import Setting
from pickysettings.core.exceptions import setting as setting_exceptions


"""
Tests pertaining to the .get_module_path() method of individual Setting objects
that are stored for each setting provided to LazySettings.

Testing for exceptions is redundant here because the first method that
.get_module_path() calls is the .get_absolute_path() method, which already
has exception tests in place.
"""


def assertModulePath(self, setting, expected):
    module_path = setting.get_module_path()

    error_message = (
        "\n"
        f"Actual Module Path: {expected}\n"
        f"Expected Absolute Path: {module_path}\n"
    )

    assert module_path == expected, error_message


def test_folder_name_like_file(create_temp_dir):
    """
    If the Setting object is initialized with a file like string structure,
    (i.e,. dev or app/settings/dev.py) BUT the actual filesystem location
    associated with that file is NOT a file, but a folder (i.e. a folder
    named dev.py) this will cause setting.get_path() to return the path
    as if it is a file but the exception will be raised when .get_absolute_path()
    is called.
    """

    # Create a Directory with File Like Name
    directory = create_temp_dir('app/settings/dev.py')
    assert pathlib.PosixPath(str(directory)).is_dir()

    base_path = pathlib.PosixPath('app/settings')
    setting = Setting('dev', base_path=base_path)
    assert str(setting.get_path()) == 'dev.py'

    # Exception Should be Raised to Indicate Path Points to Non-File
    with pytest.raises(setting_exceptions.SettingIsNotFilePath):
        setting.get_module_path()

    setting = Setting('app/settings/dev.py', base_path=None)
    assert str(setting.get_path()) == 'app/settings/dev.py'

    # Exception Should be Raised to Indicate Path Points to Non-File
    with pytest.raises(setting_exceptions.SettingIsNotFilePath):
        setting.get_module_path()


def test_without_extension(create_temp_dir, create_temp_file):
    """
    If the Setting value is just the name of the file without an
    extension, it is treated as a 1-component module path and the extension
    is assumed.

    If the Setting value is a module path with multiple components,
    the extension should be assumed.

    If the Setting value is a file path without an extension, an
    exception should be raised.
    """
    create_temp_dir('app/settings')
    create_temp_file('dev.py', directory='app/settings')

    # Test with Extensionless Filename - Treated as Module - Extension Assumed
    base_path = pathlib.PosixPath('app/settings')
    setting = Setting('dev', base_path=base_path)

    assertModulePath(setting, 'app.settings.dev')

    # Test with Module - Extension Assumed
    base_path = pathlib.PosixPath('app')
    setting = Setting('settings.dev', base_path=base_path)

    assertModulePath(setting, 'app.settings.dev')


def test_filename_with_extension(create_temp_dir, create_temp_file):

    create_temp_dir('app/settings')
    create_temp_file('dev.py', directory='app/settings')

    base_path = pathlib.PosixPath('app/settings')
    setting = Setting('dev.py', base_path=base_path)

    assertModulePath(setting, 'app.settings.dev')


def test_path_appended_to_base_dir(create_temp_dir, create_temp_file):
    """
    Setting path should be joined to base directory if there is no
    overlap between the Setting path and base directory.
    """
    create_temp_dir('app/settings')
    create_temp_file('dev.py', directory='app/settings')

    base_path = pathlib.PosixPath('app')

    # Test with Path
    setting = Setting('settings/dev.py', base_path=base_path)
    assertModulePath(setting, 'app.settings.dev')

    # Test with Module
    setting = Setting('settings.dev', base_path=base_path)
    assertModulePath(setting, 'app.settings.dev')


def test_path_relative_to_base_dir(create_temp_dir, create_temp_file):
    """
    Setting value can be relative to the base directory.
    """
    create_temp_dir('app/settings/development')
    create_temp_file('dev.py', directory='app/settings/development')

    # Test with Path
    base_path = pathlib.PosixPath('app/settings/development')
    setting = Setting('app/settings/development/dev.py', base_path=base_path)
    assertModulePath(setting, 'app.settings.development.dev')

    base_path = pathlib.PosixPath('app/settings')
    setting = Setting('app/settings/development/dev.py', base_path=base_path)
    assertModulePath(setting, 'app.settings.development.dev')

    # Test with Module
    base_path = pathlib.PosixPath('app/settings/development')
    setting = Setting('app.settings.development.dev', base_path=base_path)
    assertModulePath(setting, 'app.settings.development.dev')

    base_path = pathlib.PosixPath('app/settings')
    setting = Setting('app.settings.development.dev', base_path=base_path)
    assertModulePath(setting, 'app.settings.development.dev')
