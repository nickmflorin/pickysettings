import os
import pytest

from pickysettings import LazySettings
from pickysettings.core.exceptions import (
    BasePathDoesNotExist, BasePathIsNotDir, SettingsLoadError, SettingsNotConfigured,
    EnvVarNotFound, SettingFileDoesNotExist, EnvVarsNotFound)


"""
[x] NOTE:
--------

When creating settings that we are actually going to load with importlib,
we have to create them within the pickysettings module, so we set aside a folder
in tests/settings for this.

This is all handled by the temp_module fixture.
"""


class TestSettings:
    """
    Abstract Test Class for Organization Purposes
    Purpose: Testing the initialization of LazySettings with files specified
        via the different methods:
            (1) Command Line Args
            (2) ENV Variables
            (3) Initialization Params

    When trying to access a value on the settings object for the first time, the
    settings will be loaded for the first time (not on initialization) at which
    point any potential errors will be raised.
    """
    base_path = 'app/settings'
    module_path = 'app/settings/dev.py'  # Path where File is Created with Content

    def test_case_insensitive(self, tmp_module):

        tmp_module(self.module_path, content={
            'TEST_VARIABLE_1': 1,
            'TEST_VARIABLE_2': 5,
        })

        settings = LazySettings('dev', base_dir=self.base_path)

        assert settings.test_variable_1 == 1
        assert settings.test_variable_2 == 5

    def test_functions_ignored(self, tmp_module):

        content = """
        def sample_function():
            return 1

        TEST_VARIABLE_1 = 5
        TEST_VARIABLE_2 = 10
        """

        tmp_module(self.module_path, content=content)
        settings = LazySettings('dev', base_dir=self.base_path)

        assert settings.as_dict() == {
            'TEST_VARIABLE_1': 5,
            'TEST_VARIABLE_2': 10,
        }

    def test_imports_ignored(self, tmp_module):

        content = """
        import pathlib

        TEST_VARIABLE_1 = 5
        TEST_VARIABLE_2 = 10
        """

        tmp_module(self.module_path, content=content)
        settings = LazySettings('dev', base_dir=self.base_path)

        assert settings.as_dict() == {
            'TEST_VARIABLE_1': 5,
            'TEST_VARIABLE_2': 10,
        }

    def test_env_settings_do_not_override(self, tmp_module):
        """
        ENV settings should be overridden by any settings specified via
        initialization of the LazySettings object.
        """
        tmp_module('app/settings/dev.py', content={
            'TEST_VARIABLE_1': 1,
            'TEST_VARIABLE_2': 15,
        })

        tmp_module('app/settings/dev2.py', content={
            'TEST_VARIABLE_1': 5,
            'TEST_VARIABLE_3': 10,
        })

        os.environ['TEST_FILE1'] = 'dev2'

        settings = LazySettings('dev', base_dir=self.base_path, env_keys=['TEST_FILE1'])

        assert settings.TEST_VARIABLE_1 == 1
        assert settings.TEST_VARIABLE_2 == 15
        assert settings.TEST_VARIABLE_3 == 10

    def test_invalid_import_raises(self, tmp_module):

        invalid_content = """
        import missing_package

        TEST_VARIABLE_1 = 5
        TEST_VARIABLE_3 = 10
        """

        tmp_module('app/settings/dev.py', content=invalid_content, invalid=True)

        settings = LazySettings('dev', base_dir=self.base_path)
        with pytest.raises(SettingsLoadError) as e:
            settings.TEST_VARIABLE_1

        assert (
            [err.exc.__class__ for err in e.value.errors] == [ModuleNotFoundError])

    def test_settings_not_configured(self):
        """
        If LazySettings is initialized without any specified settings, or
        any valid ENV variables or command line arguments, SettingsNotConfigured
        should be raised to indicate that there are no settings specified.
        """
        settings = LazySettings(base_dir='app/settings.py')
        with pytest.raises(SettingsNotConfigured):
            settings.SOME_VALUE

    def test_nonexisting_path(self):
        """
        When trying to access a value on the settings object for the first time, the
        settings will be loaded.

        If the absolute path of the base directory (in this case, the temp directory
        joined with '/Users/John/settings') does not exist, an exception should be
        raised.
        """
        settings = LazySettings('dev', 'base.py', base_dir='app/settings')
        with pytest.raises(BasePathDoesNotExist):
            settings.SETTINGS_VALUE

    def test_nonexisting_file(self, tmp_module, raises_load_error):
        """
        If the base path provided to LazySettings exists, but the file corresponding
        to the Setting object does not exist, SettingFileDoesNotExist should
        be raised.

        Note that this exception actually gets triggered in the Setting object.

        [x] TODO:
        --------
        Should we test under various situations of strict load?  Should we allow
        strict load to ignore missing files as long as one valid file exists?
        """
        tmp_module('app/settings')

        settings = LazySettings('dev', base_dir=self.base_path)
        with raises_load_error(SettingFileDoesNotExist):
            settings.SETTINGS_VALUE

        # Test With Non Existing Environment Variable but Valid Init Setting
        tmp_module('app/settings/dev.py')
        os.environ['SETTINGS_FILE'] = 'dev2'

        settings = LazySettings('dev', env_keys='SETTINGS_FILE', base_dir=self.base_path)
        with raises_load_error(SettingFileDoesNotExist):
            settings.SETTINGS_VALUE

    def test_file_base_path(self, tmp_module):
        """
        If the path of the base directory (in this case, the temp directory
        joined with 'users/john/settings') indicates a file, an exception should be
        raised.
        """
        tmp_module('users/john/settings.py')
        settings = LazySettings('dev.py', base_dir='users/john/settings.py')

        with pytest.raises(BasePathIsNotDir):
            settings.SETTINGS_VALUE

    def test_env_variables_missing(self, tmp_module):
        """
        If LazySettings is initialized with ENV keys and there is no value
        in os.environ associated with those ENV keys, then the EnvVarsNotFound
        exception should be raised.
        """
        tmp_module('app/settings/dev.py')
        settings = LazySettings(env_keys=['dev'], base_dir='app/settings/dev.py')

        with pytest.raises(EnvVarsNotFound):
            settings.TEST_VARIABLE_1
