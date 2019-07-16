import os
import pytest
import sys

from tests.helpers import need_to_do

from pickysettings import LazySettings
from pickysettings.core.exceptions import *


@pytest.mark.usefixtures('file_client')
class TestFileWithExtension:
    """
    Abstract Test Class for Organization Purposes
    Purpose: Testing the initialization of LazySettings with files specified
        as simple filenames with an extension.
    """

    settings_path = 'dev.py'
    base_path = 'app/settings'
    module_path = 'app/settings/dev.py'  # Path where File is Created with Content

    def test_file_path(self, tmp_module):

        content = self.randomize_content(params=['TEST_VARIABLE_1', 'TEST_VARIABLE_2'])
        tmp_module(self.module_path, content=content.as_string)

        settings = LazySettings(self.settings_path, base_dir=self.base_path)

        assert settings.as_dict() == content.as_dict

    @need_to_do
    def test_command_file_path(self):
        pass

    def test_env_file_path(self, tmp_module):

        content = self.randomize_content(params=['TEST_VARIABLE_1', 'TEST_VARIABLE_2'])
        tmp_module(self.module_path, content=content.as_string)

        os.environ['TEST_FILE'] = self.settings_path
        settings = LazySettings(base_dir=self.base_path, env_keys='TEST_FILE')

        assert settings.as_dict() == content.as_dict

    def test_module_file_path(self, tmp_module, module_string):
        """
        Specifying an extension on a module path (i.e. app.settings.dev.py) will
        cause the extension to be treated as the filename, raising an exception.
        """
        content = self.randomize_content(params=['TEST_VARIABLE_1', 'TEST_VARIABLE_2'])
        tmp_module(self.module_path, content=content.as_string)

        settings_path = module_string(self.base_path)
        settings_path += '.py'

        settings = LazySettings(settings_path, base_dir=self.base_path)
        with pytest.raises(SettingsLoadError) as e:
            settings.TEST_VARIABLE_1

        assert [e.exc.__class__ for e in e.value.errors] == [SettingFileDoesNotExist]


@pytest.mark.usefixtures('file_client')
class TestFileWithoutExtension:
    """
    Abstract Test Class for Organization Purposes
    Purpose: Testing the initialization of LazySettings with files specified
        as simple filenames without an extension.
    """

    settings_path = 'dev'
    base_path = 'app/settings'
    module_path = 'app/settings/dev.py'  # Path where File is Created with Content

    def test_file_path(self, tmp_module):

        content = self.randomize_content(params=['TEST_VARIABLE_1', 'TEST_VARIABLE_2'])
        tmp_module(self.module_path, content=content.as_string)

        settings = LazySettings(self.settings_path, base_dir=self.base_path)

        assert settings.as_dict() == content.as_dict

    def test_command_file_path(self, tmp_module, tmpdir):

        sys.argv.append('--testargs=%s' % self.settings_path)

        content = self.randomize_content(params=['TEST_VARIABLE_1', 'TEST_VARIABLE_2'])
        tmp_module(self.module_path, content=content.as_string)

        settings = LazySettings(command_line_args='--testargs',
            base_dir=self.base_path)
        assert settings.as_dict() == content.as_dict

    def test_env_file_path(self, tmp_module):

        content = self.randomize_content(params=['TEST_VARIABLE_1', 'TEST_VARIABLE_2'])
        tmp_module(self.module_path, content=content.as_string)

        os.environ['TEST_FILE'] = self.settings_path
        settings = LazySettings(base_dir=self.base_path, env_keys='TEST_FILE')

        assert settings.as_dict() == content.as_dict


@pytest.mark.usefixtures('file_client')
class TestRelativeToBase:
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

    def test_file_path(self, tmp_module):

        content = self.randomize_content(params=['TEST_VARIABLE_1', 'TEST_VARIABLE_2'])
        tmp_module(self.module_path, content=content.as_string)

        settings = LazySettings(self.settings_path, base_dir=self.base_path)

        assert settings.as_dict() == content.as_dict

    def test_env_file_path(self, tmp_module):

        content = self.randomize_content(params=['TEST_VARIABLE_1', 'TEST_VARIABLE_2'])
        tmp_module(self.module_path, content=content.as_string)

        os.environ['TEST_FILE'] = self.settings_path
        settings = LazySettings(base_dir=self.base_path, env_keys='TEST_FILE')

        assert settings.as_dict() == content.as_dict

    def test_command_file_path(self, tmp_module, module_string):

        sys.argv.append('--testargs=%s' % self.settings_path)

        content = self.randomize_content(params=['TEST_VARIABLE_1', 'TEST_VARIABLE_2'])
        tmp_module(self.module_path, content=content.as_string)

        settings = LazySettings(base_dir=self.base_path, command_line_args='--testargs')
        assert settings.as_dict() == content.as_dict

    def test_module_file_path(self, tmp_module, module_string):

        content = self.randomize_content(params=['TEST_VARIABLE_1', 'TEST_VARIABLE_2'])
        tmp_module(self.module_path, content=content.as_string)

        settings_path = module_string(self.settings_path)
        settings = LazySettings(settings_path, base_dir=self.base_path)

        assert settings.as_dict() == content.as_dict


@pytest.mark.usefixtures('file_client')
class TestRelativeToAbsoluteBase:
    """
    Abstract Test Class for Organization Purposes
    Purpose: Testing the initialization of LazySettings with files specified
        as relative to the absolute form of the base path.

    We should be able to specify the settings file as a filepath relative to
    the absolute form of the base_dir:

        BASE_DIR = 'app/settings'
        ENV TEST_FILE = '/.../app/settings/dev.py'

    We do not need the `base_dir` parameter to be absolute.  In fact, we don't
    even need to specify it.
    """

    settings_path = 'app/settings/dev.py'
    base_path = 'app/settings'
    module_path = 'app/settings/dev.py'  # Path where File is Created with Content

    def test_file_path(self, tmp_module, tmpdir):

        content = self.randomize_content(params=['TEST_VARIABLE_1', 'TEST_VARIABLE_2'])
        tmp_module(self.module_path, content=content.as_string)

        settings = LazySettings(self.settings_path,
            base_dir=str(tmpdir.join(self.base_path)))

        assert settings.as_dict() == content.as_dict

    def test_env_file_path(self, tmp_module, tmpdir):

        content = self.randomize_content(params=['TEST_VARIABLE_1', 'TEST_VARIABLE_2'])
        tmp_module(self.module_path, content=content.as_string)

        os.environ['TEST_FILE'] = self.settings_path
        settings = LazySettings(env_keys='TEST_FILE')

        assert settings.as_dict() == content.as_dict

        settings = LazySettings(env_keys='TEST_FILE',
            base_dir=str(tmpdir.join(self.base_path)))

        assert settings.as_dict() == content.as_dict

    def test_command_file_path(self, tmp_module, tmpdir):

        sys.argv.append('--testargs=%s' % self.module_path)

        content = self.randomize_content(params=['TEST_VARIABLE_1', 'TEST_VARIABLE_2'])
        tmp_module(self.module_path, content=content.as_string)

        settings = LazySettings(command_line_args='--testargs',
            base_dir=str(tmpdir.join(self.base_path)))
        assert settings.as_dict() == content.as_dict

    def test_module_file_path(self, tmp_module, tmpdir, module_string):

        content = self.randomize_content(params=['TEST_VARIABLE_1', 'TEST_VARIABLE_2'])
        tmp_module(self.module_path, content=content.as_string)

        settings = LazySettings(module_string(self.settings_path),
            base_dir=str(tmpdir.join(self.base_path)))

        assert settings.as_dict() == content.as_dict
