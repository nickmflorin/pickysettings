import pathlib
import pytest
import os

from pickysettings.core.setting import Setting
from pickysettings.core.exceptions import *


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
        path = setting.file_path()
        assert str(path) == 'dev.py'

        setting = Setting('app.settings.dev')
        path = setting.file_path()
        assert str(path) == 'app/settings/dev.py'

    def test_path(self):
        setting = Setting('app/settings/dev.py')
        path = setting.file_path()
        assert str(path) == 'app/settings/dev.py'

    def test_absolute_path(self):
        setting = Setting('/app/settings/dev.py')
        path = setting.file_path()
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
        with pytest.raises(SettingFileIsNotFilePath):
            setting.file_path()

        setting = Setting('dev')
        path = setting.file_path()
        assert str(path) == 'dev.py'

    def test_filename_with_extension(self, tmp_module, tmpdir):
        """
        The file does not need to exist for .get_path(), but in some cases the
        directory does, since base_path will be checked.
        """
        tmp_module('app/settings/dev.py')

        setting = Setting('dev.py', base_dir=str(tmpdir.join('app/settings')))
        path = setting.file_path()
        assert str(path) == 'dev.py'

        # Having the file there doesn't really make a difference because it
        # will always treat as a file with extension unless the module path exists.
        setting = Setting('dev.py', base_dir=str(tmpdir.join('app/settings')))
        path = setting.file_path()
        assert str(path) == 'dev.py'

    def test_invalid_setting(self):

        setting = Setting('filename.')
        with pytest.raises(SettingFileLoadError):
            setting.file_path()

        # Folders cannot have "." in them, at least not right now.
        setting = Setting('app/settings.dev/dev.py')
        with pytest.raises(SettingFileLoadError):
            setting.file_path()

        setting = Setting('/prod.dev.py')
        with pytest.raises(SettingFileLoadError):
            setting.file_path()

        setting = Setting('.gitignore')
        with pytest.raises(UnsupportedFileType):
            setting.file_path()

    def test_treats_as_module_path(self, tmp_module):
        """
        When the "2 Component Problem" is applicable, if the file associated
        with a module path exists, the setting should be treated as a module
        path.

        If the file assocaited with the module path does not exist, the setting
        will be treated as a file, even if the file is invalid.  An exception
        will be raised downstream, in the absolute_file_path() method.
        """
        tmp_module('app/settings/deploy/prod.py')

        setting = Setting('deploy.prod', base_dir='app/settings')
        path = setting.file_path()
        assert str(path) == 'deploy/prod.py'

        setting = Setting('deploy.debug', base_dir='app/settings')
        path = setting.file_path()
        assert str(path) == 'deploy.debug'


class TestGetModulePath:
    """
    Abstract Test Class for Organization Purposes
    Purpose: Testing the .module_file_path() method on the Setting object.

    Testing for exceptions is redundant here because the first method that
    .module_file_path() calls is the .get_absolute_path() method, which already
    has exception tests in place.
    """

    def assertModulePath(self, setting, expected):
        module_path = setting.module_file_path()

        error_message = (
            "\n"
            f"Actual Module Path: {expected}\n"
            f"Expected Absolute Path: {module_path}\n"
        )

        assert module_path == expected, error_message

    def test_folder_name_like_file(self, tmp_module):
        """
        If the Setting object is initialized with a file like string structure,
        (i.e,. dev or app/settings/dev.py) BUT the actual filesystem location
        associated with that file is NOT a file, but a folder (i.e. a folder
        named dev.py) this will cause setting.get_path() to return the path
        as if it is a file but the exception will be raised when .get_absolute_path()
        is called.
        """

        # Create a Directory with File Like Name
        directory = tmp_module('app/settings')
        directory = directory.joinpath('dev.py')
        directory.mkdir()

        assert directory.is_dir()

        setting = Setting('dev', base_dir='app/settings')
        assert str(setting.file_path()) == 'dev.py'

        # Exception Should be Raised to Indicate Path Points to Non-File
        with pytest.raises(SettingFileIsNotFilePath):
            setting.module_file_path()

        setting = Setting('app/settings/dev.py')
        assert str(setting.file_path()) == 'app/settings/dev.py'

        # Exception Should be Raised to Indicate Path Points to Non-File
        with pytest.raises(SettingFileIsNotFilePath):
            setting.module_file_path()

    def test_without_extension(self, tmp_module):
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
        tmp_module('app/settings/dev.py')

        # Test with Extensionless Filename - Treated as Module - Extension Assumed
        setting = Setting('dev', base_dir='app/settings')
        self.assertModulePath(setting, 'app.settings.dev')

        # Test with Module - Extension Assumed
        setting = Setting('settings.dev', base_dir='app')
        self.assertModulePath(setting, 'app.settings.dev')

    def test_filename_with_extension(self, tmp_module):

        tmp_module('app/settings/dev.py')
        setting = Setting('dev', base_dir='app/settings')
        self.assertModulePath(setting, 'app.settings.dev')

    def test_path_appended_to_base_dir(self, tmp_module):
        """
        Setting path should be joined to base directory if there is no
        overlap between the Setting path and base directory.
        """
        tmp_module('app/settings/dev.py')

        # Test with Path
        setting = Setting('settings/dev.py', base_dir='app')
        self.assertModulePath(setting, 'app.settings.dev')

        # Test with Module
        setting = Setting('settings.dev', base_dir='app')
        self.assertModulePath(setting, 'app.settings.dev')

    def test_path_relative_to_base_dir(self, tmp_module):
        """
        Setting value can be relative to the base directory.
        """
        tmp_module('app/settings/development/dev.py')

        # Test with Path
        setting = Setting('app/settings/development/dev.py', base_dir='app/settings/development')
        self.assertModulePath(setting, 'app.settings.development.dev')

        setting = Setting('app/settings/development/dev.py', base_dir='app/settings')
        self.assertModulePath(setting, 'app.settings.development.dev')

        # Test with Module
        setting = Setting('app.settings.development.dev', base_dir='app/settings/development')
        self.assertModulePath(setting, 'app.settings.development.dev')

        setting = Setting('app.settings.development.dev', base_dir='app/settings')
        self.assertModulePath(setting, 'app.settings.development.dev')


@pytest.fixture
def assertAbsPath(tmpdir):

    def assertPath(setting, path):

        absolute_path = setting.absolute_file_path()
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
    Purpose: Testing the .absolute_file_path() method on the Setting object.
    """

    def test_module_caveats(self, tmp_module, assertAbsPath):
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
        tmp_module('app/settings/dev.py')

        # Caveat 1
        setting = Setting('develop.dev', base_dir='app')
        with pytest.raises(UnsupportedFileType):
            setting.absolute_file_path()

        # Caveat 2 (Not really a caveat, this is kind of expected).
        setting = Setting('settings.dev.ini', base_dir='app')
        with pytest.raises(SettingFileDirDoesNotExist):
            setting.absolute_file_path()

    def test_module_treated_as_path(self, tmp_module, assertAbsPath):
        """
        When dealing with the "2 Component Problem", if the setting is specified
        as a module string but the module cannot be found, it will be treated
        as a file with the given extension.
        """
        tmp_module('app/settings/develop/dev.py')
        setting = Setting('develop.develop_settings', base_dir='app/settings')

        with pytest.raises(UnknownFileType):
            setting.absolute_file_path()

    def test_file_does_not_exist(self, tmp_module, assertAbsPath):
        """
        The existence of the directory containing the file pointed to by the
        setting is checked before the existence of the file, so if the directory
        exists, non-existent files should raise SettingsFileDoesNotExist.
        """
        tmp_module('app/settings/dev.py')

        # # Test with Path
        # setting = Setting('prod.py', base_dir='app/settings')
        # with pytest.raises(SettingFileDoesNotExist):
        #     setting.absolute_file_path()

        # Test with Module
        setting = Setting('prod', base_dir='app/settings')
        with pytest.raises(SettingFileDoesNotExist):
            setting.absolute_file_path()

    def test_directory_does_not_exist(self, tmp_module, assertAbsPath):
        """
        The existence of the directory containing the file pointed to by the
        setting is checked before the existence of the file, so if the directory
        does not exist, non-existent files/directories should raise
        SettingFileDirDoesNotExist.
        """
        tmp_module('app/settings/dev.py')

        # Test with Path
        setting = Setting('develop/dev.py', base_dir='app')
        with pytest.raises(SettingFileDirDoesNotExist):
            setting.absolute_file_path()

        # Test with Module
        setting = Setting('settings.develop.dev', base_dir='app')
        with pytest.raises(SettingFileDirDoesNotExist):
            setting.absolute_file_path()

    def test_file_without_extension(self, tmp_module, assertAbsPath):
        """
        If the Setting value is just the name of the file without an
        extension, it is treated as a 1-component module path and the extension
        is assumed.

        If the Setting value is a module path with multiple components,
        the extension should be assumed.

        If the Setting value is a file path without an extension, an
        exception should be raised.
        """
        tmp_module('app/settings/dev.py')

        # Test with Extensionless Filename - Extension Assumed
        setting = Setting('dev', base_dir='app/settings')
        assertAbsPath(setting, 'app/settings/dev.py')

        # Test with Module - Extension Assumed
        setting = Setting('settings.dev', base_dir='app')
        assertAbsPath(setting, 'app/settings/dev.py')

        # Test with Path - Extension Required, Otherwise thinks it's a directory.
        setting = Setting('settings/dev', base_dir='app')
        with pytest.raises(SettingFileIsNotFilePath):
            setting.absolute_file_path()

    def test_file_with_extension(self, tmp_module, assertAbsPath):

        tmp_module('app/settings/dev.py')

        setting = Setting('dev.py', base_dir='app/settings')
        assertAbsPath(setting, 'app/settings/dev.py')

    def test_unsupported_filetype(self, tmp_module, assertAbsPath):

        tmp_module('app/settings/dev.ini')

        setting = Setting('dev.ini', base_dir='app/settings')
        with pytest.raises(UnsupportedFileType):
            setting.absolute_file_path()

        setting = Setting('settings/dev.ini', base_dir='app')
        with pytest.raises(UnsupportedFileType):
            setting.absolute_file_path()

        # Exception should be raised even if the file with the given extension
        # exists.
        tmp_module('app/settings/dev.abc')

        setting = Setting('develop.abc', base_dir='app/settings')
        with pytest.raises(UnsupportedFileType):
            setting.absolute_file_path()

    def test_unknown_filetype(self, tmp_module, assertAbsPath):
        tmp_module('app/settings/development/dev.uac')

        setting = Setting('settings/dev.uac', base_dir='app')
        with pytest.raises(UnknownFileType):
            setting.absolute_file_path()

        setting = Setting('dev.uac', base_dir='app/settings')
        with pytest.raises(UnknownFileType):
            setting.absolute_file_path()

    def test_path_relativity(self, tmp_module, assertAbsPath):
        """
        Tests various situations in which both the absolute forms and non-absolute
        forms of the base path and file path are specified and whether or not
        the Setting instance can correctly determine the file path based on the
        relativity of the different path forms to one another.

        [x] TODO:
        --------
        Split these tests apart.
        """
        file_path = 'app/settings/development/dev.py'
        base_path = 'app/settings'

        tmp_module(file_path)

        absolute_file_path = pathlib.PosixPath(file_path).absolute()
        absolute_base_path = pathlib.PosixPath(base_path).absolute()

        # Path Not Absolute
        # Base Path Not Absolute
        # Path Relative to Base Path
        setting = Setting(file_path, base_path)
        assertAbsPath(setting, 'app/settings/development/dev.py')

        # Path Absolute
        # Base Path Absolute
        # Absolute Path Relative to Absolute Base Path
        setting = Setting(absolute_file_path, absolute_base_path)
        assertAbsPath(setting, file_path)

        # Path Not Absolute
        # Base Path Absolute
        # Absolute Form of Path Relative to Absolute Base Path
        setting = Setting(file_path, absolute_base_path)
        assertAbsPath(setting, 'app/settings/development/dev.py')

        # Path Absolute
        # Base Path Not Absolute
        # Path Relative to Absolute Form of Base Path
        setting = Setting(absolute_file_path, base_path)
        assertAbsPath(setting, 'app/settings/development/dev.py')

        # If path is not absolute and not relative to either the base path or
        # the absolute base path, it should be joined with the base path.
        setting = Setting('development/dev.py', base_path)
        assertAbsPath(setting, 'app/settings/development/dev.py')

        setting = Setting('development/dev.py', absolute_base_path)
        assertAbsPath(setting, 'app/settings/development/dev.py')

        # If the path is not relative to the absolute base path or the base
        # path, overlapping paths will not be recognized and will raise
        # SettingFileDirDoesNotExist.
        setting = Setting('development/dev.py', 'app/settings/development')
        with pytest.raises(SettingFileDirDoesNotExist):
            setting.absolute_file_path()

        # Test with Path
        setting = Setting('settings/development/dev.py', base_dir='app')
        assertAbsPath(setting, 'app/settings/development/dev.py')

        # Test with Module
        setting = Setting('settings.development.dev', base_dir='app')
        assertAbsPath(setting, 'app/settings/development/dev.py')

        setting = Setting('development.dev', base_dir='app/settings')
        assertAbsPath(setting, 'app/settings/development/dev.py')
