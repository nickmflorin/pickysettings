from termx.ext.utils import ConditionalString, humanize_list

from .base import ComposeError
from .fields import FieldError, FieldErrorMeta, FieldCodes


class SettingsNotConfigured(ComposeError):
    """
    Raised when the settings are collecting the file references from various
    sources and none are retrieved.
    """

    def __str__(self):
        return "Settings not configured."


class EnvVarNotFound(ComposeError):
    """
    Raised when a non-default ENV variable key used to initialize LazySettings
    is not found in os.environ.

    Usually (at least for now) we will just use this to issue warnings when
    not performing strict validation - ``EnvVarsNotFound`` will be raised if
    strict validation fails with at least one occurence of ``EnvVarNotFound``.
    """

    def __init__(self, env_key):
        self._env_key = env_key

    def __str__(self):
        return f"The key {self._env_key} does not exist in os.environ."


class EnvVarsNotFound(ComposeError):
    """
    Raised when at least 1 specified (non-default) ENV variable key used to
    initialize LazySettings is not found in os.environ, when validation is
    strict.

    Comprised of one or more instances of EnvVarNotFound.
    """

    def __init__(self, errors):
        self._errors = errors

    def __str__(self):
        keys = [err._env_key for err in self._errors]
        return f"The keys {humanize_list(keys)} do not exist in os.environ."


class FieldInitializationError(ComposeError, FieldError, metaclass=FieldErrorMeta):

    class Codes(FieldCodes):

        EXPECTED_FIELD_INSTANCE = ConditionalString('The field', FieldError.FIELD, 'is not a Field instance')
        UNEXPECTED_FIELD_INSTANCE = ConditionalString('The field', FieldError.FIELD, 'should not be a Field instance')
        # Duplicate Field Should Not be Raised Since dir(module) Returns Dict
        # DUPLICATE_FIELD = ConditionalString('The field', FieldError.FIELD, 'was already set in this file')
        CANNOT_ADD_CONFIGURABLE_FIELD = ConditionalString('Cannot add configurable field',
            FieldError.FIELD, 'to a non-configurable set')
