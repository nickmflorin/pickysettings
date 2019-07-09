import pathlib
import pytest
import os

from pickysettings.core.setting import Setting
from pickysettings.core.exceptions import setting as setting_exceptions


class TestGetPath:

    """
    Abstract Test Class for Organization Purposes
    Purpose: Testing the .get_path() method on the Setting object.

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

    def test_module_path(self):
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

    def test_path(self):
        setting = Setting('app/settings/dev.py')
        path = setting.get_path()
        assert str(path) == 'app/settings/dev.py'

    def test_absolute_path(self):
        setting = Setting('/app/settings/dev.py')
        path = setting.get_path()
        assert str(path) == '/app/settings/dev.py'

    def test_without_extension(self):
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

    def test_filename_with_extension(self, create_temp_dir, create_temp_file):
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

    def test_invalid_setting(self):

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

    def test_treats_as_module_path(self, mock_cwd, create_temp_dir, create_temp_file):
        """
        When the "2 Component Problem" is applicable, if the file associated
        with a module path exists, the setting should be treated as a module
        path.

        If the file assocaited with the module path does not exist, the setting
        will be treated as a file, even if the file is invalid.  An exception
        will be raised downstream, in the get_absolute_path() method.
        """
        mock_cwd()

        create_temp_dir('app/settings/deploy')
        create_temp_file('prod.py', directory='app/settings/deploy')

        base_path = pathlib.PosixPath('app/settings')

        setting = Setting('deploy.prod', base_path=base_path)
        path = setting.get_path()
        assert str(path) == 'deploy/prod.py'

        setting = Setting('deploy.debug', base_path=base_path)
        path = setting.get_path()
        assert str(path) == 'deploy.debug'


class TestGetModulePath:
    """
    Abstract Test Class for Organization Purposes
    Purpose: Testing the .get_module_path() method on the Setting object.

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

    def test_folder_name_like_file(self, mock_cwd, create_temp_dir):
        """
        If the Setting object is initialized with a file like string structure,
        (i.e,. dev or app/settings/dev.py) BUT the actual filesystem location
        associated with that file is NOT a file, but a folder (i.e. a folder
        named dev.py) this will cause setting.get_path() to return the path
        as if it is a file but the exception will be raised when .get_absolute_path()
        is called.
        """

        mock_cwd()

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

    def test_without_extension(self, mock_cwd, create_temp_dir, create_temp_file):
        """
        Part of "2-Component Problem"

        If the Setting value is just the name of the file without an
        extension, it is treated as a 1-component module path and the extension
        is assumed.

        If the Setting value is a module path with multiple components,
        the extension should be assumed.

        If the Setting value is a file path without an extension, an
        exception should be raised.
        """
        mock_cwd()

        create_temp_dir('app/settings')
        create_temp_file('dev.py', directory='app/settings')

        # Test with Extensionless Filename - Treated as Module - Extension Assumed
        base_path = pathlib.PosixPath('app/settings')
        setting = Setting('dev', base_path=base_path)

        self.assertModulePath(setting, 'app.settings.dev')

        # Test with Module - Extension Assumed
        base_path = pathlib.PosixPath('app')
        setting = Setting('settings.dev', base_path=base_path)

        self.assertModulePath(setting, 'app.settings.dev')

    def test_filename_with_extension(self, mock_cwd, create_temp_dir, create_temp_file):

        mock_cwd()

        create_temp_dir('app/settings')
        create_temp_file('dev.py', directory='app/settings')

        base_path = pathlib.PosixPath('app/settings')
        setting = Setting('dev', base_path=base_path)

        self.assertModulePath(setting, 'app.settings.dev')

    def test_path_appended_to_base_dir(self, mock_cwd, create_temp_dir, create_temp_file):
        """
        Setting path should be joined to base directory if there is no
        overlap between the Setting path and base directory.
        """
        mock_cwd()

        create_temp_dir('app/settings')
        create_temp_file('dev.py', directory='app/settings')

        base_path = pathlib.PosixPath('app')

        # Test with Path
        setting = Setting('settings/dev.py', base_path=base_path)
        self.assertModulePath(setting, 'app.settings.dev')

        # Test with Module
        setting = Setting('settings.dev', base_path=base_path)
        self.assertModulePath(setting, 'app.settings.dev')

    def test_path_relative_to_base_dir(self, mock_cwd, create_temp_dir, create_temp_file):
        """
        Setting value can be relative to the base directory.
        """
        mock_cwd()

        create_temp_dir('app/settings/development')
        create_temp_file('dev.py', directory='app/settings/development')

        # Test with Path
        base_path = pathlib.PosixPath('app/settings/development')
        setting = Setting('app/settings/development/dev.py', base_path=base_path)
        self.assertModulePath(setting, 'app.settings.development.dev')

        base_path = pathlib.PosixPath('app/settings')
        setting = Setting('app/settings/development/dev.py', base_path=base_path)
        self.assertModulePath(setting, 'app.settings.development.dev')

        # Test with Module
        base_path = pathlib.PosixPath('app/settings/development')
        setting = Setting('app.settings.development.dev', base_path=base_path)
        self.assertModulePath(setting, 'app.settings.development.dev')

        base_path = pathlib.PosixPath('app/settings')
        setting = Setting('app.settings.development.dev', base_path=base_path)
        self.assertModulePath(setting, 'app.settings.development.dev')


@pytest.fixture
def assertAbsPath(tmpdir):

    def assertPath(setting, path):

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
    return assertPath


class TestGetAbsolutePath:
    """
    Abstract Test Class for Organization Purposes
    Purpose: Testing the .get_absolute_path() method on the Setting object.
    """

    def test_module_caveats(self, mock_cwd, create_temp_dir, create_temp_file, assertAbsPath):
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
        mock_cwd()

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

    def test_module_treated_as_path(self, mock_cwd, create_temp_dir, create_temp_file, assertAbsPath):
        """
        When dealing with the "2 Component Problem", if the setting is specified
        as a module string but the module cannot be found, it will be treated
        as a file with the given extension.
        """
        mock_cwd()

        create_temp_dir('app/settings/develop')
        create_temp_file('dev.py', directory='app/settings/develop')

        base_path = pathlib.PosixPath('app/settings')
        setting = Setting('develop.develop_settings', base_path=base_path)

        with pytest.raises(setting_exceptions.UnknownFileType):
            setting.get_absolute_path()

    def test_file_does_not_exist(self, mock_cwd, create_temp_dir, create_temp_file, assertAbsPath):
        """
        The existence of the directory containing the file pointed to by the
        setting is checked before the existence of the file, so if the directory
        exists, non-existent files should raise SettingsFileDoesNotExist.
        """
        mock_cwd()

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

    def test_directory_does_not_exist(self, mock_cwd, create_temp_dir, create_temp_file, assertAbsPath):
        """
        The existence of the directory containing the file pointed to by the
        setting is checked before the existence of the file, so if the directory
        does not exist, non-existent files/directories should raise
        SettingDirDoesNotExist.
        """
        mock_cwd()

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

    def test_file_without_extension(self, mock_cwd, create_temp_dir, create_temp_file, assertAbsPath):
        """
        If the Setting value is just the name of the file without an
        extension, it is treated as a 1-component module path and the extension
        is assumed.

        If the Setting value is a module path with multiple components,
        the extension should be assumed.

        If the Setting value is a file path without an extension, an
        exception should be raised.
        """
        mock_cwd()

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

    def test_file_with_extension(self, mock_cwd, create_temp_dir, create_temp_file, assertAbsPath):

        mock_cwd()

        create_temp_dir('app/settings')
        create_temp_file('dev.py', directory='app/settings')

        base_path = pathlib.PosixPath('app/settings')
        setting = Setting('dev.py', base_path=base_path)

        assertAbsPath(setting, 'app/settings/dev.py')

    def test_unsupported_filetype(self, mock_cwd, create_temp_dir, create_temp_file, assertAbsPath):

        mock_cwd()

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

    def test_unknown_filetype(self, mock_cwd, create_temp_dir, create_temp_file, assertAbsPath):
        mock_cwd()

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

    def test_path_appended_to_base_dir(self, mock_cwd, create_temp_dir, create_temp_file, assertAbsPath):
        """
        Setting path should be joined to base directory if there is no
        overlap between the Setting path and base directory.
        """
        mock_cwd()

        create_temp_dir('app/settings')
        create_temp_file('dev.py', directory='app/settings')

        base_path = pathlib.PosixPath('app')

        # Test with Path
        setting = Setting('settings/dev.py', base_path=base_path)
        assertAbsPath(setting, 'app/settings/dev.py')

        # Test with Module
        setting = Setting('settings.dev', base_path=base_path)
        assertAbsPath(setting, 'app/settings/dev.py')

    def test_path_overlaps_base_dir(self, mock_cwd, create_temp_dir, create_temp_file, assertAbsPath):
        """
        If the setting value overlaps the base directory but the two paths
        are not relative, which would mean being the same path, InvalidSetting
        should be raised.

        If there is overlap, we cannot safely concatenate the setting path to
        the base path.
        """
        mock_cwd()

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

    def test_path_relative_to_abs_base_dir(self, mock_cwd, create_temp_dir, create_temp_file, assertAbsPath):
        """
        Setting value can be relative to the absolute base directory.
        """
        mock_cwd()

        create_temp_dir('app/settings/development')
        create_temp_file('dev.py', directory='app/settings/development')

        # Test with Path
        setting = Setting(os.path.join(os.getcwd(), 'app/settings/development/dev.py'),
            base_dir=os.path.join(os.getcwd(), 'app/settings/development'))
        assertAbsPath(setting, 'app/settings/development/dev.py')
