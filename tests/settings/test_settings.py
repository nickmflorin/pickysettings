import pytest

from pickysettings import LazySettings

from pickysettings.core.exceptions import initialization as init_exceptions


def test_settings_not_configured():
    """
    If LazySettings is initialized without any specified settings, or
    any valid ENV variables or command line arguments, SettingsNotConfigured
    should be raised to indicate that there are no settings specified.
    """
    settings = LazySettings(base_dir='Users/John/settings.py')
    with pytest.raises(init_exceptions.SettingsNotConfigured):
        settings.SOME_VALUE


def test_nonexisting_base_path():
    """
    When trying to access a value on the settings object for the first time, the
    settings will be loaded.

    If the absolute path of the base directory (in this case, the temp directory
    joined with '/Users/John/settings') does not exist, an exception should be
    raised.
    """
    settings = LazySettings('dev', 'base.py', base_dir='Users/John/settings')
    with pytest.raises(init_exceptions.MissingSettingsDir):
        settings.SETTINGS_VALUE


def test_file_base_path(create_temp_dir, create_temp_file):
    """
    When trying to access a value on the settings object for the first time, the
    settings will be loaded.

    If the absolute path of the base directory (in this case, the temp directory
    joined with '/Users/John/settings') indicates a file, an exception should be
    raised.
    """
    create_temp_dir('Users/John')
    create_temp_file('settings.py', directory='Users/John')

    settings = LazySettings('dev.py', base_dir='Users/John/settings.py')

    with pytest.raises(init_exceptions.InvalidSettingsDir):
        settings.SETTINGS_VALUE
