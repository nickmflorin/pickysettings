import pathlib

from .initialization import SettingsInitializationError


class SettingFileLoadError(SettingsInitializationError):
    """
    Only raised if we have already validated that the file exists in the right
    location and there is an error importing it.
    """

    def __init__(self, settings_file, exc):
        self._file = settings_file
        self._exc = exc


class InvalidSetting(SettingsInitializationError):
    """
    Raised pertaining to a single invalid setting.
    """

    def __init__(self, value):
        self.value = value
        if isinstance(self.value, pathlib.Path):
            self.value = str(self.value)
        self.path = pathlib.Path(self.value)

    def __str__(self):
        return f"The setting {self.value} is invalid."


class SettingIsNotFilePath(InvalidSetting):

    def __str__(self):
        return f"The setting {self.value} does not point to a file."


class SettingDirDoesNotExist(InvalidSetting):
    """
    Raised in regard to the `base_path` parameter, if the absolute path of
    the `base_path` directory does not exist or does not indicate a directory.

    This can also be raised for settings specifications that provide a file
    along with a relative directory.
    """

    def __str__(self):
        return f"The directory {self.path.parent.as_posix()} does not exist."


class SettingFileDoesNotExist(InvalidSetting):
    """
    Raised if the file pointed to by the specification does not exist.
    """

    def __str__(self):
        return f"The file at path {self.path.as_posix()} does not exist."


class UnsupportedFileType(InvalidSetting):
    """
    Raised if the file pointed to by the specification is a non-Python or
    non-supported file type.
    """

    def __str__(self):
        return "Unsupported file type %s." % self.path.suffix


class UnknownFileType(InvalidSetting):
    """
    Raised if the file pointed to by the specification is a non-Python or
    unknown file type.
    """

    def __str__(self):
        return "Unknown file type %s." % self.path.suffix
