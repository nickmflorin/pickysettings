import os
import pathlib
import pytest

from pickysettings.core.setting import Setting
from pickysettings.core.exceptions import setting as setting_exceptions


"""
Tests pertaining to the .get_absolute_path() method of individual Setting objects
that are stored for each setting provided to LazySettings.
"""


def assertAbsPath(self, tmpdir, setting, path):

    absolute_path = setting.get_absolute_path()
    expected = os.path.join(str(tmpdir), path)

    expected_rel_path = pathlib.Path(expected).relative_to(tmpdir)
    absolute_rel_path = absolute_path.relative_to(tmpdir)

    error_message = (
        "\n"
        f"Actual Absolute Path: {str(absolute_rel_path)}\n"
        f"Expected Absolute Path: {str(expected_rel_path)}\n"
    )

    assert str(absolute_path) == expected, error_message


def test_module_caveats(create_temp_dir, create_temp_file):
    """
    Tests certain weird/unpreventable behavior due to the trouble deciphering
    a filename with extension vs. a two-component module string.

    At the end of the day, an exception will always be raised.  However,
    due to the "2 Component Problem", there are certain caveats where the
    exception raised might not be indicative of the actual problem.

    Caveats:
    -------
        (1) `develop.dev` will be treated as a file with extension `.dev`,
            so a different exception will be raised.
        (2) `settings.dev.ini` will be treated as a module string and raise
            an exception that "dev" directory does not exist.
    """
    create_temp_dir('app/settings')
    create_temp_file('dev.py', directory='app/settings')

    base_path = pathlib.PosixPath('app')

    # Caveat 1
    setting = Setting('develop.dev', base_path=base_path)
    with pytest.raises(setting_exceptions.UnsupportedFileType):
        setting.get_absolute_path()

    # Caveat 2 (Not really a caveat, this is kind of expected).
    setting = Setting('settings.dev.ini', base_path=base_path)
    with pytest.raises(setting_exceptions.SettingDirDoesNotExist):
        setting.get_absolute_path()


def test_module_treated_as_path(create_temp_dir, create_temp_file):
    """
    When dealing with the "2 Component Problem", if the setting is specified
    as a module string but the module cannot be found, it will be treated
    as a file with the given extension.
    """
    create_temp_dir('app/settings/develop')
    create_temp_file('dev.py', directory='app/settings/develop')

    base_path = pathlib.PosixPath('app/settings')
    setting = Setting('develop.develop_settings', base_path=base_path)

    with pytest.raises(setting_exceptions.UnknownFileType):
        setting.get_absolute_path()


def test_file_does_not_exist(create_temp_dir, create_temp_file):
    """
    The existence of the directory containing the file pointed to by the
    setting is checked before the existence of the file, so if the directory
    exists, non-existent files should raise SettingsFileDoesNotExist.
    """
    create_temp_dir('app/settings')
    create_temp_file('dev.py', directory='app/settings')

    base_path = pathlib.PosixPath('app/settings')

    # Test with Path
    setting = Setting('prod.py', base_path=base_path)
    with pytest.raises(setting_exceptions.SettingFileDoesNotExist):
        setting.get_absolute_path()

    # Test with Module
    setting = Setting('prod', base_path=base_path)
    with pytest.raises(setting_exceptions.SettingFileDoesNotExist):
        setting.get_absolute_path()


def test_directory_does_not_exist(create_temp_dir, create_temp_file):
    """
    The existence of the directory containing the file pointed to by the
    setting is checked before the existence of the file, so if the directory
    does not exist, non-existent files/directories should raise
    SettingDirDoesNotExist.
    """
    create_temp_dir('app/settings')
    create_temp_file('dev.py', directory='app/settings')

    base_path = pathlib.PosixPath('app')

    # Test with Path
    setting = Setting('develop/dev.py', base_path=base_path)
    with pytest.raises(setting_exceptions.SettingDirDoesNotExist):
        setting.get_absolute_path()

    # Test with Module
    setting = Setting('settings.develop.dev', base_path=base_path)
    with pytest.raises(setting_exceptions.SettingDirDoesNotExist):
        setting.get_absolute_path()


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

    # Test with Extensionless Filename - Extension Assumed
    base_path = pathlib.PosixPath('app/settings')
    setting = Setting('dev', base_path=base_path)

    assertAbsPath(setting, 'app/settings/dev.py')

    # Test with Module - Extension Assumed
    base_path = pathlib.PosixPath('app')

    setting = Setting('settings.dev', base_path=base_path)
    assertAbsPath(setting, 'app/settings/dev.py')

    # Test with Path - Extension Required, Otherwise thinks it's a directory.
    setting = Setting('settings/dev', base_path=base_path)
    with pytest.raises(setting_exceptions.SettingIsNotFilePath):
        setting.get_absolute_path()


def test_filename_with_extension(create_temp_dir, create_temp_file):

    create_temp_dir('app/settings')
    create_temp_file('dev.py', directory='app/settings')

    base_path = pathlib.PosixPath('app/settings')
    setting = Setting('dev.py', base_path=base_path)

    assertAbsPath(setting, 'app/settings/dev.py')


def test_unsupported_filetype(create_temp_dir, create_temp_file):

    create_temp_dir('app/settings')
    create_temp_file('dev.ini', directory='app/settings')

    base_path = pathlib.PosixPath('app/settings')
    setting = Setting('dev.ini', base_path=base_path)

    with pytest.raises(setting_exceptions.UnsupportedFileType):
        setting.get_absolute_path()

    base_path = pathlib.PosixPath('app')
    setting = Setting('settings/dev.ini', base_path=base_path)

    with pytest.raises(setting_exceptions.UnsupportedFileType):
        setting.get_absolute_path()

    # Exception should be raised even if the file with the given extension
    # exists.
    create_temp_dir('app/settings/develop')
    create_temp_file('dev.abc', directory='app/settings/develop')

    base_path = pathlib.PosixPath('app/settings')
    setting = Setting('develop.abc', base_path=base_path)

    with pytest.raises(setting_exceptions.UnsupportedFileType):
        setting.get_absolute_path()


def test_unknown_filetype(create_temp_dir, create_temp_file):

    create_temp_dir('app/settings')
    create_temp_file('dev.uac', directory='app/settings')

    base_path = pathlib.PosixPath('app')
    setting = Setting('settings/dev.uac', base_path=base_path)

    with pytest.raises(setting_exceptions.UnknownFileType):
        setting.get_absolute_path()

    base_path = pathlib.PosixPath('app/settings')
    setting = Setting('dev.uac', base_path=base_path)

    with pytest.raises(setting_exceptions.UnknownFileType):
        setting.get_absolute_path()


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
    assertAbsPath(setting, 'app/settings/dev.py')

    # Test with Module
    setting = Setting('settings.dev', base_path=base_path)
    assertAbsPath(setting, 'app/settings/dev.py')


def test_path_overlaps_base_dir(create_temp_dir, create_temp_file):
    """
    If the setting value overlaps the base directory but the two paths
    are not relative, which would mean being the same path, InvalidSetting
    should be raised.

    If there is overlap, we cannot safely concatenate the setting path to
    the base path.
    """
    create_temp_dir('app/settings/development')
    create_temp_file('dev.py', directory='app/settings/development')

    base_path = pathlib.PosixPath('app/settings')

    # Test with Path
    setting = Setting('settings/development/dev.py', base_path=base_path)
    with pytest.raises(setting_exceptions.InvalidSetting):
        setting.get_absolute_path()

    # Test with Module
    setting = Setting('settings.development.dev', base_path=base_path)
    with pytest.raises(setting_exceptions.InvalidSetting):
        setting.get_absolute_path()


def test_path_relative_to_base_dir(create_temp_dir, create_temp_file):
    """
    Setting value can be relative to the base directory.
    """
    create_temp_dir('app/settings/development')
    create_temp_file('dev.py', directory='app/settings/development')

    # Test with Path
    base_path = pathlib.PosixPath('app/settings/development')
    setting = Setting('app/settings/development/dev.py', base_path=base_path)
    assertAbsPath(setting, 'app/settings/development/dev.py')

    base_path = pathlib.PosixPath('app/settings')
    setting = Setting('app/settings/development/dev.py', base_path=base_path)
    assertAbsPath(setting, 'app/settings/development/dev.py')

    # Test with Module
    base_path = pathlib.PosixPath('app/settings/development')
    setting = Setting('app.settings.development.dev', base_path=base_path)
    assertAbsPath(setting, 'app/settings/development/dev.py')

    base_path = pathlib.PosixPath('app/settings')
    setting = Setting('app.settings.development.dev', base_path=base_path)
    assertAbsPath(setting, 'app/settings/development/dev.py')
