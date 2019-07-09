import os
import pytest

from tests.mgmt import need_to_do

from pickysettings import LazySettings
from pickysettings.core.exceptions import (
    initialization as init_exceptions, setting as setting_exceptions)

from .base import TestSettingsBase


class TestFileWithExtension(TestSettingsBase):
    """
    Abstract Test Class for Organization Purposes
    Purpose: Testing the initialization of LazySettings with files specified
        as simple filenames with an extension.
    """

    settings_path = 'dev.py'
    base_path = 'app/settings'
    module_path = 'app/settings/dev.py'  # Path where File is Created with Content

    def test_file_path(self, temp_module):

        temp_module(self.module_path, content={
            'TEST_VARIABLE_1': 1,
            'TEST_VARIABLE_2': 5,
        })

        settings = LazySettings(self.settings_path, base_dir=self.base_path)

        assert settings.TEST_VARIABLE_1 == 1
        assert settings.TEST_VARIABLE_2 == 5

    @need_to_do
    def test_command_file_path(self):
        pass

    def test_env_file_path(self, temp_module):

        temp_module(self.module_path, content={
            'TEST_VARIABLE_1': 1,
            'TEST_VARIABLE_2': 5,
        })

        os.environ['TEST_FILE'] = self.settings_path
        settings = LazySettings(base_dir=self.base_path, env_keys='TEST_FILE')

        assert settings.TEST_VARIABLE_1 == 1
        assert settings.TEST_VARIABLE_2 == 5

    def test_module_file_path(self, temp_module, module_string):
        """
        Specifying an extension on a module path (i.e. app.settings.dev.py) will
        cause the extension to be treated as the filename, raising an exception.
        """
        temp_module(self.module_path, content={
            'TEST_VARIABLE_1': 1,
            'TEST_VARIABLE_2': 5,
        })

        settings_path = module_string(self.base_path)
        settings_path += '.py'

        settings = LazySettings(settings_path, base_dir=self.base_path)
        with pytest.raises(setting_exceptions.SettingFileDoesNotExist):
            settings.TEST_VARIABLE_1


class TestFileWithoutExtension(TestSettingsBase):
    """
    Abstract Test Class for Organization Purposes
    Purpose: Testing the initialization of LazySettings with files specified
        as simple filenames without an extension.
    """

    settings_path = 'dev'
    base_path = 'app/settings'
    module_path = 'app/settings/dev.py'  # Path where File is Created with Content

    def test_file_path(self, temp_module):

        temp_module(self.module_path, content={
            'TEST_VARIABLE_1': 1,
            'TEST_VARIABLE_2': 5,
        })

        settings = LazySettings(self.settings_path, base_dir=self.base_path)

        assert settings.TEST_VARIABLE_1 == 1
        assert settings.TEST_VARIABLE_2 == 5

    @need_to_do
    def test_command_file_path(self):
        pass

    def test_env_file_path(self, temp_module):

        temp_module(self.module_path, content={
            'TEST_VARIABLE_1': 1,
            'TEST_VARIABLE_2': 5,
        })

        os.environ['TEST_FILE'] = self.settings_path
        settings = LazySettings(base_dir=self.base_path, env_keys='TEST_FILE')

        assert settings.TEST_VARIABLE_1 == 1
        assert settings.TEST_VARIABLE_2 == 5


class TestRelativeToBase(TestSettingsBase):
    """
    Abstract Test Class for Organization Purposes
    Purpose: Testing the initialization of LazySettings with files specified
        as relative to the non-absolute form of the base path.

    We should be able to specify the settings file as a filepath relative to
    the non-absolute form of the base_dir:

        BASE_DIR = 'tests/tmp_modules/app/settings'
        ENV TEST_FILE = 'tests/tmp_modules/app/settings/dev.py'
    """

    settings_path = 'app/settings/dev.py'
    base_path = 'app/settings'
    module_path = 'app/settings/dev.py'  # Path where File is Created with Content

    def _settings_path(self, path, tests_module_path):
        return tests_module_path.joinpath(path)

    def test_file_path(self, temp_module):

        temp_module(self.module_path, content={
            'TEST_VARIABLE_1': 1,
            'TEST_VARIABLE_2': 5,
        })

        settings = LazySettings(self.settings_path, base_dir=self.base_path)

        assert settings.TEST_VARIABLE_1 == 1
        assert settings.TEST_VARIABLE_2 == 5

    def test_env_file_path(self, temp_module):

        temp_module(self.module_path, content={
            'TEST_VARIABLE_1': 1,
            'TEST_VARIABLE_2': 5,
        })

        os.environ['TEST_FILE'] = self.settings_path
        settings = LazySettings(base_dir=self.base_path, env_keys='TEST_FILE')

        assert settings.TEST_VARIABLE_1 == 1
        assert settings.TEST_VARIABLE_2 == 5

    @need_to_do
    def test_command_file_path(self):
        pass

    # This Currently Caught a Bug!
    def test_module_file_path(self, temp_module, module_string):

        temp_module(self.module_path, content={
            'TEST_VARIABLE_1': 1,
            'TEST_VARIABLE_2': 5,
        })

        settings_path = module_string(self.settings_path)
        settings = LazySettings(settings_path, base_dir=self.base_path)

        assert settings.TEST_VARIABLE_1 == 1
        assert settings.TEST_VARIABLE_2 == 5


class TestRelativeToAbsoluteBase(TestSettingsBase):
    """
    Abstract Test Class for Organization Purposes
    Purpose: Testing the initialization of LazySettings with files specified
        as relative to the absolute form of the base path.

    We should be able to specify the settings file specified by the ENV variable
    as a filepath relative to the absolute form of the base_dir:

        BASE_DIR = 'tests/tmp_modules/app/settings'
        ENV TEST_FILE = '/.../tests/tmp_modules/app/settings/dev.py'

    We do not need the `base_dir` parameter to be absolute.  In fact, we don't
    even need to specify it.
    """

    settings_path = 'app/settings/dev.py'
    base_path = 'app/settings'
    module_path = 'app/settings/dev.py'  # Path where File is Created with Content

    def _settings_path(self, path, tests_module_path):
        return tests_module_path.absolute().joinpath(path)

    def _base_path(self, path, tests_module_path):
        return tests_module_path.joinpath(path)

    def test_file_path(self, temp_module):

        temp_module(self.module_path, content={
            'TEST_VARIABLE_1': 1,
            'TEST_VARIABLE_2': 5,
        })

        settings = LazySettings(self.settings_path, base_dir=self.base_path)

        assert settings.TEST_VARIABLE_1 == 1
        assert settings.TEST_VARIABLE_2 == 5

    def test_env_file_path(self, temp_module):

        temp_module(self.module_path, content={
            'TEST_VARIABLE_1': 1,
            'TEST_VARIABLE_2': 5,
        })

        os.environ['TEST_FILE'] = self.settings_path
        settings = LazySettings(env_keys='TEST_FILE')

        assert settings.TEST_VARIABLE_1 == 1
        assert settings.TEST_VARIABLE_2 == 5

        settings = LazySettings(base_dir=self.base_path, env_keys='TEST_FILE')

        assert settings.TEST_VARIABLE_1 == 1
        assert settings.TEST_VARIABLE_2 == 5

    @need_to_do
    def test_command_file_path(self):
        pass

    @need_to_do
    def test_module_file_path(self):
        pass
