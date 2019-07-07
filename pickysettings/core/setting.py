import importlib
import inspect
import os
import pathlib

from pickysettings.lib.extensions import EXTENSIONS
from pickysettings.lib.utils import paths_overlap

from pickysettings.core.fields import ConstantField
from pickysettings.core.fields.base import FieldABC

from .exceptions import setting as exceptions, FieldInitializationError
from .utils import Storable


class Setting(Storable):
    """
    Represents a single reference to a settings file, whether provided directly
    to LazySettings, provided as an ENV variable or as a command line argument.

    The reference can be specified in several different ways in order to promote
    flexibility of the module:

    (1) Relative to Base Path
        - specification = Users/settings/filename.py
        - base_path = Users/settings
    (2) Appended to Base Path (base_path = Users)
        - settings/filename.py
            >>> Users/settings/filename.py
        - filename
            >>> Users/filename.py
        - filename.py
            >>> Users/filename.py
    (3) Absolute Path
        - /root/Users/settings/filename.py
            >>> /root/Users/settings/filename.py
        - /root/Users/settings/filename
            >>> /root/Users/settings/filename.py
    (4) Module Path
        - <module>.<module>.<file_name>
    """

    DEFAULT_FILE_EXT = 'py'

    def __init__(self, value, base_path=None):

        self._base_path = base_path
        self._value = value

        # Variable that indicates whether or not the values from the loaded file
        # associated with this Setting instance have been stored in the LazySettings
        # object/container.
        self._stored = False
        super(Setting, self).__init__()

    @property
    def value(self):
        return self._value

    def __setitem__(self, key, value):
        if not isinstance(value, FieldABC):
            value = ConstantField(value)
        super(Setting, self).__setitem__(key, value)

    def as_dict(self):
        return self._store

    def load(self):
        """
        [x] TODO:
        --------
        Should we maybe also catch errors here as well, similar to below,
        and allow valid/invalid settings to be loaded independently?
        """
        original = self.copy()
        self.clear()

        module_string = self.get_module_path()

        try:
            module = importlib.import_module(module_string)
        except (ImportError, TypeError) as e:
            # Just in case there is an error reloading, maintain original settings.
            # Do we really need this if we are just loading the settings once?
            # Maybe for configuration but not loading?
            # self.update(**original)
            raise exceptions.SettingFileLoadError(module_string, e)
        else:
            for param in (s for s in dir(module) if not s.startswith('_')):
                param_value = getattr(module, param)

                # Ignore Import Statements of Modules and Import Statements of Functions
                if not inspect.ismodule(param_value) and not inspect.isfunction(param_value):
                    self.__setitem__(param, param_value)

    def raise_for_absolute_path(self, absolute_path):

        if len(absolute_path.suffixes) != 1:
            raise RuntimeError('Paths with multiple suffixes should be weeded out.')

        if absolute_path.suffix != '.py':
            if absolute_path.suffix in EXTENSIONS:
                raise exceptions.UnsupportedFileType(absolute_path)
            else:
                raise exceptions.UnknownFileType(absolute_path)

        if not absolute_path.parent.exists():
            raise exceptions.SettingDirDoesNotExist(absolute_path.parent)

        if not absolute_path.exists():
            raise exceptions.SettingFileDoesNotExist(absolute_path)

        # This can happen if the original path points to a directory with a file
        # like name (i.e. a directory named folder.py).
        if not absolute_path.is_file():
            raise exceptions.SettingIsNotFilePath(absolute_path)

    def _join_with_suffix(self, *parts):
        joined = "/".join(list(parts))
        return pathlib.PosixPath(joined).with_suffix('.%s' % self.DEFAULT_FILE_EXT)

    def get_module_path(self):

        # Get Path of Specification File Relative to Working Directory
        cwd_path = pathlib.PosixPath(os.getcwd())
        absolute_path = self.get_absolute_path()

        try:
            module_file_path = absolute_path.relative_to(cwd_path)
        except ValueError:
            # [x] TODO: Make sure we are checking this ahead of time.
            raise RuntimeError(
                'The specification file path should always be relative to the '
                'current working directory and this should be checked ahead of '
                'time.'
            )
        else:
            module_file_path = module_file_path.with_suffix('')
            return '.'.join(module_file_path.parts)

    def get_absolute_path(self, path=None):

        file_path = path or self.get_path()
        if file_path.is_absolute():
            self.raise_for_absolute_path(file_path)
            return file_path

        if self._base_path:
            try:
                file_path = file_path.relative_to(self._base_path)
            except ValueError:
                if not paths_overlap(self._base_path, file_path):
                    file_path = self._base_path.joinpath(file_path)
                else:
                    raise exceptions.InvalidSetting(
                        "The path %s is not relative to the base %s."
                        % (file_path.as_posix(), self._base_path.as_posix())
                    )
            else:
                file_path = self._base_path.joinpath(file_path)

        file_path = file_path.absolute()
        self.raise_for_absolute_path(file_path)
        return file_path

    def get_path(self):
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
        value = "%s" % self._value

        if '.' in value:
            parts = value.split('.')
            if '/' in value:
                if len(parts) != 2:
                    raise exceptions.InvalidSetting(value)
                return pathlib.PosixPath(value)  # Suffix Required
            else:
                # Only Valid Possibilities at This Point:
                #   (1) filename.py
                #   (2) module.filename
                #   (3) module.submodule.filename
                if len(parts) == 2:
                    if parts[0] == '':
                        raise exceptions.UnsupportedFileType(value)  # e.g. .gitignore, .git
                    elif parts[1] == '':
                        raise exceptions.InvalidSetting(value)  # e.g. "filename."
                    else:
                        path = self._join_with_suffix(*parts)
                        try:
                            self.get_absolute_path(path=path)
                        except exceptions.InvalidSetting:
                            return pathlib.PosixPath(value)
                        else:
                            return path

                else:
                    # Guaranteed to be Module Path at This Point
                    # (i.e. module.submodule.filename)
                    #  (Assumes suffix is not included in module path)
                    return self._join_with_suffix(*parts)

        else:
            # Either just a filename without extension or a path without a file.
            if '/' in value:
                raise exceptions.SettingIsNotFilePath(value)
            return pathlib.PosixPath(value).with_suffix('.%s' % self.DEFAULT_FILE_EXT)
