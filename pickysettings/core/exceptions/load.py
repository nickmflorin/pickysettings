import pathlib
import traceback

from termx import settings
from termx.fmt import style

from .base import LoadError


class SettingFileLoadError(LoadError):
    """
    Wrapper for more general case of any issue with a setting file specificaiton
    that causes issues getting the absolute path and loading.

    These errors are conglomerated together and outputted via the wrapped
    SettingsLoadError.

    Only raised directly if we have already validated that the file exists in
    the right location and there is an error importing it.
    """
    __detail__ = ""

    def __init__(self, path, detail=None, exc=None):

        self.path = path
        self.detail = detail
        self.exc = exc

    def __str__(self):
        if self.__detail__:
            return self.__detail__
        return (
            f"An error occured loading the setting file at {str(self.path)}:\n"
            f"{self.detail}"
        )


class BasePathIsNotDir(SettingFileLoadError):
    """
    Raised in regard to the `base_dir` parameter.
    If the `base_dir` points to a file instead of a directory.
    """

    @property
    def __detail__(self):
        return f"The directory at {str(self.path)} is invalid."


class BasePathDoesNotExist(SettingFileLoadError):
    """
    Raised in regard to the `base_dir` parameter.
    If the `base_dir` points to a directory that does not exist.
    """
    @property
    def __detail__(self):
        return f"The directory at {str(self.path)} does not exist."


class InvalidSettingFile(SettingFileLoadError):
    """
    Base exception class for exceptions that are raised due to an invalid
    specification for the `settings_file` parameter.
    """
    @property
    def __detail__(self):
        return "The setting file %s is not valid." % str(self.path)


class SettingFileIsNotFilePath(InvalidSettingFile):
    """
    Raised if the file pointed to by the settings_file is a directory and not
    a file.
    """
    @property
    def __detail__(self):
        return "The path %s does not indicate a file." % str(self.path)


class SettingFileDirDoesNotExist(InvalidSettingFile):
    """
    Raised if the file pointed to by the settings_file is in a directory that
    does not exist.
    """
    @property
    def __detail__(self):
        return "The parent directory %s does not exist." % str(self.path.parent)


class SettingFileDoesNotExist(InvalidSettingFile):
    """
    Raised if the file pointed to by the settings_file does not exist.
    """
    @property
    def __detail__(self):
        return "The file %s does not exist." % str(self.path)


class UnsupportedFileType(InvalidSettingFile):
    """
    Raised if the file pointed to by the specification is a non-Python or
    non-supported file type.
    """
    @property
    def __detail__(self):
        if not isinstance(self.path, pathlib.Path):
            pt = pathlib.Path(self.path)
            if pt.suffix:
                return "Unsupported file type %s." % pt.suffix
            return "Unsupported file type %s." % str(pt)
        return "Unsupported file type %s." % self.path.suffix


class InvalidFileFormat(InvalidSettingFile):
    @property
    def __detail__(self):
        return "The settings file %s is not of a valid format." % str(self.path)


class UnknownFileType(InvalidSettingFile):
    """
    Raised if the file pointed to by the specification is a non-Python or
    unknown file type.
    """

    @property
    def __detail__(self):
        if not isinstance(self.path, pathlib.Path):
            pt = pathlib.Path(self.path)
            if pt.suffix:
                return "Unknown file type %s." % pt.suffix
            return "Unknown file type %s." % str(pt)
        return "Unknown file type %s." % self.path.suffix


class SettingsLoadError(LoadError):
    """
    Raised when there is an error importing a specific settings module with
    importlib, but the file does exist.

    SettingsLoadError is comprised of one or more SettingFileLoadError and is
    raised conditionally based on the presence of at least one valid settings
    file and the validation object's values.
    """

    def __init__(self, errors, debug=False):
        self.errors = errors
        self._debug = debug

    def _error_message(self, err, index):

        message_lines = [f" ({index + 1}) [{settings.colors.NORMAL_GRAY(err.path)}]"]
        if not self._debug:
            exc_name = style.bold(err.__class__.__name__)
            message_lines.append(f"     {exc_name}: {str(err)}")
        else:
            # Unclear if this is working, hard to repliace in tests by creating
            # exception directly.
            message_lines.extend(traceback.format_tb(
                err._exc.__traceback__,
                limit=100,
            ))
        return message_lines

    @property
    def header(self):
        content = f"Could Not Load {len(self.errors)} Settings File(s)"
        return ["\n%s" % settings.formats.fail(content)]

    @property
    def footer(self):
        content = "(Initialize settings with `debug=True` for full traceback)"
        if not self._debug:
            return [settings.colors.light_gray(content)]
        return []

    @property
    def body(self):
        body_lines = []
        for i, err in enumerate(self.errors):
            body_lines.extend(self._error_message(err, i))
        return body_lines

    def __str__(self):
        lines = self.header + self.body + self.footer
        return "\n".join(lines)
