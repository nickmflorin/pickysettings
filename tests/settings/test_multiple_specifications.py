import os
import pytest

from pickysettings import LazySettings
from pickysettings.core.exceptions import *


class TestMultipleSettings:
    """
    Abstract Test Class for Organization Purposes
    Purpose: Testing the initialization of LazySettings with multiple settings
        files from potentially different sources or the same sources.
    """

    base_path = 'app/settings'

    def test_multiple_files(self, tmp_module):

        tmp_module('app/settings/dev.py', content={
            'TEST_VARIABLE_1': 1,
            'TEST_VARIABLE_2': 15,
        })

        tmp_module('app/settings/dev2.py', content={
            'TEST_VARIABLE_1': 5,
            'TEST_VARIABLE_3': 10,
        })

        settings = LazySettings('dev', 'dev2', base_dir=self.base_path)

        assert settings.TEST_VARIABLE_1 == 5
        assert settings.TEST_VARIABLE_2 == 15
        assert settings.TEST_VARIABLE_3 == 10

    def test_multiple_env_files(self, tmp_module):

        tmp_module('app/settings/dev.py', content={
            'TEST_VARIABLE_1': 1,
            'TEST_VARIABLE_2': 15,
        })

        tmp_module('app/settings/dev2.py', content={
            'TEST_VARIABLE_1': 5,
            'TEST_VARIABLE_3': 10,
        })

        os.environ['TEST_FILE1'] = 'dev'
        os.environ['TEST_FILE2'] = 'dev2'

        settings = LazySettings(base_dir=self.base_path,
            env_keys=['TEST_FILE1', 'TEST_FILE2'])

        assert settings.TEST_VARIABLE_1 == 5
        assert settings.TEST_VARIABLE_2 == 15
        assert settings.TEST_VARIABLE_3 == 10

    def test_multiple_files_with_invalid(self, tmp_module):
        """
        If LazySettings encounters an invalid/unimportable settings file during
        load, it's treatment of the initialization depends on the value of the
        `validation` __init__ param.

        If `validation = strict` (by default), SettingsLoadError should be
        raised when the LazySettings instance attempts to load the settings
        files.

        If `validation = none`:
            - If there is at least one valid file that was loaded, LazySettings
              should issue a warning for the invalid files encountered.
            - If there are no valid files loaded, SettingsLoadError should still
              raised.
        """
        valid_content = """
        import pathlib

        TEST_VARIABLE_1 = 1
        TEST_VARIABLE_2 = 15
        """

        invalid_content = """
        import missing_package

        TEST_VARIABLE_1 = 5
        TEST_VARIABLE_3 = 10
        """

        tmp_module('app/settings/dev.py', content=valid_content)
        tmp_module('app/settings/dev2.py', content=invalid_content, invalid=True)
        tmp_module('app/settings/dev3.py', content=invalid_content, invalid=True)

        # Condition: `validation = strict`,  one file invalid.
        # Expected: SettingsLoadError raised
        settings = LazySettings('dev', 'dev2', base_dir=self.base_path)
        with pytest.raises(SettingsLoadError) as e:
            settings.TEST_VARIABLE_1

        assert ([err.exc.__class__ for err in e.value.errors] ==
            [ModuleNotFoundError])

        # Condition: `validation = none`, one file invalid.
        # Expected: SettingsLoadError not raised
        settings = LazySettings('dev', 'dev2', base_dir=self.base_path, validation=None)

        assert settings.TEST_VARIABLE_1 == 1
        assert settings.TEST_VARIABLE_2 == 15

        # Condition: `validation = strict`, both files invalid.
        # Expected: SettingsLoadError raised (value of `validation` is irrelevant).
        settings = LazySettings('dev3', 'dev2', base_dir=self.base_path)
        with pytest.raises(SettingsLoadError) as e:
            settings.TEST_VARIABLE_1

        assert ([err.exc.__class__ for err in e.value.errors] ==
            [ModuleNotFoundError, ModuleNotFoundError])

        # Condition: `validation = none`, both files invalid.
        # Expected: SettingsLoadError raised (value of `validation` is irrelevant).
        settings = LazySettings('dev3', 'dev2', base_dir=self.base_path, validation=None)
        with pytest.raises(SettingsLoadError) as e:
            settings.TEST_VARIABLE_1

        assert ([err.exc.__class__ for err in e.value.errors] ==
            [ModuleNotFoundError, ModuleNotFoundError])
