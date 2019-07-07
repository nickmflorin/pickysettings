import traceback

from termx import settings
from termx.fmt import style
from termx.ext.utils import ConditionalString, humanize_list

from .base import pickysettingsError
from .fields import FieldError, FieldErrorMeta, FieldCodes


class SettingsInitializationError(pickysettingsError):
    pass


class SettingsNotConfigured(SettingsInitializationError):
    """
    Raised when the settings are collecting the file references from various
    sources and none are retrieved.
    """

    def __str__(self):
        return "Settings not configured."


class InvalidSettingsDir(SettingsInitializationError):
    """
    Raised when the base directory specified for the LazySettings object
    points to a file instead of a directory.
    """

    def __init__(self, path):
        self.path = path

    def __str__(self):
        return f"The directory at {self.path.as_posix()} is invalid."


class MissingSettingsDir(InvalidSettingsDir):
    """
    Raised when the base directory specified for the LazySettings object
    does not exist.
    """

    def __str__(self):
        return f"The directory at {self.path.as_posix()} does not exist."


class MissingEnvironmentKeys(SettingsInitializationError):

    def __init__(self, keys):
        self._keys = keys

    def __str__(self):
        return "The keys %s are not set as ENV variables." % humanize_list(self._keys)


class SettingsLoadError(SettingsInitializationError):
    """
    Raised when we are in `strict_load` mode and there is an error importing
    a specific settings module with importlib, but the file does exist.  Also
    raised when not in `strict_load` mode if there isn't any valid settings
    modules that were able to be loaded.

    A SettingFileLoadError will result in SettingsLoadError provided the above
    conditions regarding `strict_load` mode are met.
    """

    def __init__(self, errors, debug=False):
        self._errors = errors
        self._debug = debug

    def _error_message(self, err, index):
        message_lines = [f" ({index + 1}) [{settings.colors.NORMAL_GRAY(err._file)}]"]
        if not self._debug:
            exc_name = style.bold(err._exc.__class__.__name__)
            message_lines.append(f"     {exc_name}: {str(err._exc)}")
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
        content = f"Could Not Load {len(self._errors)} Settings File(s)"
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
        for i, err in enumerate(self._errors):
            body_lines.extend(self._error_message(err, i))
        return body_lines

    def __str__(self):
        lines = self.header + self.body + self.footer
        return "\n".join(lines)


class FieldInitializationError(SettingsInitializationError, FieldError, metaclass=FieldErrorMeta):

    class Codes(FieldCodes):

        EXPECTED_FIELD_INSTANCE = ConditionalString('The field', FieldError.FIELD, 'is not a Field instance')
        UNEXPECTED_FIELD_INSTANCE = ConditionalString('The field', FieldError.FIELD, 'should not be a Field instance')
        # Duplicate Field Should Not be Raised Since dir(module) Returns Dict
        # DUPLICATE_FIELD = ConditionalString('The field', FieldError.FIELD, 'was already set in this file')
        CANNOT_ADD_CONFIGURABLE_FIELD = ConditionalString('Cannot add configurable field',
            FieldError.FIELD, 'to a non-configurable set')
