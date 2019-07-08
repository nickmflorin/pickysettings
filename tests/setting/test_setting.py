import pytest

from pickysettings import LazySettings
from pickysettings.core.exceptions import setting as setting_exceptions


def test_nonexisting_file(create_temp_dir):
    """
    If the base path provided to LazySettings exists, but the file corresponding
    to the Setting object does not exist, SettingFileDoesNotExist should
    be raised.
    """
    create_temp_dir('Users/John/settings')

    settings = LazySettings('dev', base_dir='Users/John/settings')
    with pytest.raises(setting_exceptions.SettingFileDoesNotExist):
        settings.SETTINGS_VALUE
