import importlib
import inspect
import os
import pathlib

from pickysettings.lib.extensions import EXTENSIONS

from pickysettings.core.fields import ConstantField
from pickysettings.core.fields.base import FieldABC

from .exceptions import (
    SettingFileLoadError, BasePathIsNotDir, BasePathDoesNotExist,
    UnsupportedFileType, UnknownFileType, SettingFileDirDoesNotExist,
    SettingFileIsNotFilePath, SettingFileDoesNotExist, InvalidFileFormat,
    InvalidSettingFile)

from .utils import FieldStorable


class Setting(FieldStorable):
    """
    Represents a single reference to a settings file, whether provided directly
    to LazySettings, provided as an ENV variable or as a command line argument.
    """

    DEFAULT_FILE_EXT = 'py'

    def __init__(self, settings_file, base_dir=None):
        """
        The settings_file and base_dir can be specified in several different
        ways in order to promote flexibility of the module.

        Treatment of `settings_file`:

            (1) Local File Path

                (1a) Relative to Base Path
                    - settings_file = Users/settings/dev/filename.py
                    - base_path = Users/settings

                    >>> Users/settings/dev/filename.py

                (1b) Appended to Base Path
                    - settings_file = dev/filename.py
                    - base_path = Users/settings

                    >>> Users/settings/dev/filename.py

            (2) Absolute File Path
                    The value of `base_dir` will not be used directly, but if
                    specified, the `settings_file` must be relative to the
                    absolute form of the `base_dir`.

                        - settings_file = /root/Users/settings/filename.py

            (3) Module Path
                Treated like a Local File Path (1).
                    - <module>.<module>.<file_name>
        """
        self._file_path = None
        self._absolute_file_path = None
        self._module_file_path = None

        self._base_dir = base_dir

        self._settings_file = settings_file
        if not isinstance(self._settings_file, str):
            if isinstance(self._settings_file, pathlib.Path):
                self._settings_file = str(self._settings_file)
            else:
                raise ValueError('Setting file must be a valid str or pathlib.Path instance.')

        # Variable that indicates whether or not the values from the loaded file
        # associated with this Setting instance have been stored in the LazySettings
        # object/container.
        self._stored = False
        super(Setting, self).__init__()

    def base_path(self):
        """
        [x] NOTE:
        --------
        We could simplify the conditional below, but we want to keep the different
        legs of the conditional separate for now just in case we have to incorporate
        additional logic based on the str vs. pathlib.Path() specification of
        base_dir.
        """
        if self._base_dir:
            if isinstance(self._base_dir, pathlib.Path):
                # Not Sure if Necessary - Instantiating pathlib.Path() creates
                # a PosixPath, but we might have to take OS into consideration
                # here.
                if not isinstance(self._base_dir, pathlib.PosixPath):
                    return pathlib.PosixPath(self._base_dir)
                else:
                    return self._base_dir
            else:
                return pathlib.PosixPath(self._base_dir)

    def absolute_base_path(self):
        """
        Returns the absolute form of the base_path, generated from the provided
        `base_dir` argument on init.

        Raises
        ------
        BasePathIsNotDir
            Raised if the absolute form of the specified `base_path` points to a
            file instead of a directory.

        BasePathDoesNotExist
            Raised if the absolute form of the specified `base_path` does not exist.
        """
        base_path = self.base_path()
        if base_path:

            absolute_base_path = base_path.absolute()
            if absolute_base_path.is_file():
                raise BasePathIsNotDir(absolute_base_path)

            if not absolute_base_path.exists():
                raise BasePathDoesNotExist(absolute_base_path)

            return absolute_base_path

    def settings_file(self):
        return self._settings_file

    def file_path(self):
        """
        Returns the raw string file path specified on initialization into a
        pathlib.PosixPath() instance on the filesystem.

        Raises
        ------
        InvalidFileFormat
            If the specified file is some general invalid form that cannot be
            parsed correctly:
                - name.
                - module/submodule.name.py
                - /folder.subfolder/filename.py
        UnsupportedFileType
            If the specified file is of the form '.name'
                - .gitignore
                - .env
        SettingIsNotFilePath
            If the specified file has '/' in the string but does not have a '.':
                - /folder/subfolder/filename
                - /folder/subfolder
        """
        if not self._file_path:
            self._file_path = self._get_file_path()
        return self._file_path

    def absolute_file_path(self):
        """
        Returns the absolute form of the file path.

        Will "intelligently" try to figure out the relationship between `file_path`
        and `base_path` allowing the `file_path` to be specified as either
        relative to the `absolute_base_path` or the `base_path`, or appended
        to the `base_path`.

        Raises
        ------
        SettingFileLoadError
            If the base_path is specified and either the file path is absolute
            and not relative to the absolute base path, or the base_path is not
            absolute but is not relative to the base_path or it's absolute form
            is not relative to the absolute_base_path.
        UnsupportedFileType
            If the file extension is recognized as a valid file extension but
            not supported.
        UnknownFileType
            If the file extension is not recognized as a valid extension.
        SettingDirDoesNotExist
            The absolute path of the directory containing the file does not exist.
        SettingFileDoesNotExist
            The absolute path of the file does not exist.
        SettingIsNotFilePath
            If the original path specified as a string points to a directory
            with a file like name (i.e. app/settings/file.py where file.py is
            a directory).
        """
        if not self._absolute_file_path:
            self._absolute_file_path = self._get_absolute_file_path()
        return self._absolute_file_path

    def module_file_path(self):
        """
        Returns the module importable string form of the file path relative to
        the current working directory.

        Ex.
        >>> setting.absolute_file_path
        >>> '/root/users/app/settings.py'

        >>> os.getcwd()
        >>> '/root/users'

        >>> setting.module_file_path
        >>> app.settings
        """
        if not self._module_file_path:
            self._module_file_path = self._get_module_file_path()
        return self._module_file_path

    def __setitem__(self, key, value):
        if not isinstance(value, FieldABC):
            value = ConstantField(value)
        super(Setting, self).__setitem__(key, value)

    def as_dict(self):
        return self._store

    def load(self):
        """
        Loads the module generated from the `settings_file` parameter and
        populates the Setting instance with the data.

        If an exception is raised due to the specific `setting_file` parameter,
        we catch it and generalize the error, letting the containing LazySettings
        object handle it.

        Raises
        ------
        InvalidSettingFile
            If the module cannot be imported or there are other errors converting
            the `settings_file` parameter to an appropriate module path.

            All raised errors are extensions of SettingFileLoadError, which
            we reraise as a normalized SettingFileLoadError with the underlying
            exception.  This makes it easier for the LazySettings object to
            handle the errors in a more predictable and systematic way.

        BasePathIsNotDir
            Raised if the absolute form of the specified `base_path` points to a
            file instead of a directory.

            Raised immediately because it applies to all setting objects in the
            LazySettings instance.

        BasePathDoesNotExist
            Raised if the absolute form of the specified `base_path` does not exist.

            Raised immediately because it applies to all setting objects in the
            LazySettings instance.
        """
        try:
            module_string = self.module_file_path()
        except InvalidSettingFile as e:
            raise InvalidSettingFile(self.settings_file(), exc=e)
        else:
            try:
                module = importlib.import_module(module_string)
            except (ImportError, TypeError) as e:
                raise InvalidSettingFile(self.settings_file(), exc=e)
            else:
                for param in (s for s in dir(module) if not s.startswith('_')):
                    param_value = getattr(module, param)

                    # Ignore Import Statements of Modules and Import Statements of Functions
                    if not inspect.ismodule(param_value) and not inspect.isfunction(param_value):
                        self.__setitem__(param, param_value)

    def _get_file_path(self):
        """
        This method converts the raw specification into an absolute PosixPath
        on the filesystem.

        "2 Component Problem"
        --------------------
        There is no string manipulation method to differentiate between a
        filename with an extension and a 2-component module string:
            (1) filename.ext
            (2) settings.filename

        To solve this problem, we first assume it is a module path and check
        if the absolute path generated based on that assumption exists.  If it
        does not, we treat as a file path.

        [x] TODO:
        --------
        Make sure that checks for '/' in the value are appropriate across
        operating systems.
        """
        def join_with_suffix(*parts):
            joined = "/".join(list(parts))
            return pathlib.PosixPath(joined).with_suffix('.%s' % self.DEFAULT_FILE_EXT)

        settings_file = self.settings_file()
        if '.' in settings_file:
            parts = settings_file.split('.')

            if '/' in settings_file:
                if len(parts) != 2:
                    raise InvalidFileFormat(settings_file)
                return pathlib.PosixPath(settings_file)  # Suffix Required
            else:
                # Only Valid Possibilities at This Point:
                #   (1) filename.py
                #   (2) module.filename
                #   (3) module.submodule.filename
                if len(parts) == 2:
                    if parts[0] == '':
                        raise UnsupportedFileType(settings_file)  # e.g. .gitignore, .git
                    elif parts[1] == '':
                        raise InvalidFileFormat(settings_file)  # e.g. "filename."
                    else:
                        path = join_with_suffix(*parts)
                        try:
                            self._get_absolute_file_path(path=path)
                        except SettingFileLoadError:
                            return pathlib.PosixPath(settings_file)
                        else:
                            return path
                else:
                    # Guaranteed to be Module Path at This Point
                    return join_with_suffix(*parts)
        else:
            # Either just a filename without extension or a path without a file.
            if '/' in settings_file:
                raise SettingFileIsNotFilePath(settings_file)
            return pathlib.PosixPath(settings_file).with_suffix('.%s' % self.DEFAULT_FILE_EXT)

    def _get_absolute_file_path(self, path=None):
        """
        For the specified settings file path, and potentially base path, determines
        what the absolute path of the file is.
        """

        def raise_for_absolute_path(absolute_path):

            if len(absolute_path.suffixes) != 1:
                raise RuntimeError('Paths with multiple suffixes should be weeded out.')

            if absolute_path.suffix != '.py':
                if absolute_path.suffix in EXTENSIONS:
                    raise UnsupportedFileType(absolute_path)
                else:
                    raise UnknownFileType(absolute_path)

            if not absolute_path.parent.exists():
                raise SettingFileDirDoesNotExist(absolute_path.parent)

            if not absolute_path.exists():
                raise SettingFileDoesNotExist(absolute_path)

            # This can happen if the original path points to a directory with a file
            # like name (i.e. a directory named folder.py).
            if not absolute_path.is_file():
                raise SettingFileIsNotFilePath(absolute_path)

        file_path = path or self.file_path()
        base_path = self.absolute_base_path()

        if base_path:
            if file_path.is_absolute():
                try:
                    file_path.relative_to(self.absolute_base_path())
                except ValueError:
                    raise SettingFileLoadError(file_path, detail=(
                        "The path %s is not relative to the absolute base path %s."
                        % (str(file_path), str(self.absolute_base_path()))
                    ))
                else:
                    raise_for_absolute_path(file_path)
                    return file_path
            else:
                try:
                    relative_path = file_path.relative_to(self.base_path())
                except ValueError:
                    absolute_file_path = file_path.absolute()
                    try:
                        relative_path = absolute_file_path.relative_to(self.absolute_base_path())
                    except ValueError:
                        # If the filepath is not absolute and cannot be found to be relative
                        # to the base path or absolute base path, we append it to the
                        # base path.
                        file_path = self.base_path().joinpath(file_path)
                        absolute_file_path = file_path.absolute()
                        raise_for_absolute_path(absolute_file_path)
                        return absolute_file_path
                    else:
                        # Example:
                        #   absolute_base_path = '/root/users/app/settings'
                        #   file_path = 'app/settings/development/dev.py'
                        #   absolute_file_path = '/root/users/app/settings/development/dev.py'
                        #   relative_path = 'development/dev.py'
                        absolute_file_path = self.absolute_base_path().joinpath(relative_path)
                        raise_for_absolute_path(absolute_file_path)
                        return absolute_file_path
                else:
                    # Example:
                    #   base_path = 'app/settings'
                    #   file_path = 'app/settings/development/dev.py'
                    #   relative_path = 'development/dev.py'
                    file_path = self.base_path().joinpath(relative_path)
                    absolute_file_path = file_path.absolute()
                    raise_for_absolute_path(absolute_file_path)
                    return absolute_file_path
        else:
            absolute_file_path = file_path
            if not file_path.is_absolute():
                absolute_file_path = file_path.absolute()
            raise_for_absolute_path(absolute_file_path)
            return absolute_file_path

    def _get_module_file_path(self):
        """
        Temporarily raises ValueError if the absolute file path is not relative
        to the current working directory, which should not happen.

        [x] TODO:
        ---------
        Make sure we are checking this ahead of time.
        Then we should remove this check and just let the ValueError be
        raised, since it shouldn't be.
        """
        # Get Path of Specification File Relative to Working Directory
        cwd_path = pathlib.PosixPath(os.getcwd())

        try:
            module_file_path = self.absolute_file_path().relative_to(cwd_path)
        except ValueError:
            raise ValueError(
                'The specification file path should always be relative to the '
                'current working directory and this should be checked ahead of '
                'time.'
            )
        else:
            module_file_path = module_file_path.with_suffix('')
            return '.'.join(module_file_path.parts)
