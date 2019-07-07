from termx.ext.utils import ConditionalString

from .base import pickysettingsError
from .fields import FieldError, FieldErrorMeta, FieldCodes


class SettingConfigurationError(pickysettingsError):
    """
    General base class that is used if parameters that are used to initialize
    the LazySettings object result in an invalid configuration, such as a
    `base_dir` that does not exist.
    """
    pass


class FieldConfigurationError(SettingConfigurationError, FieldError, metaclass=FieldErrorMeta):

    class Codes(FieldCodes):

        # This shouldn't really be needed since we define all required fields in system settings.
        REQUIRED_FIELD = ConditionalString("The field", FieldError.FIELD, "is required.")
        EXCEEDS_MAX = ConditionalString("The value", FieldError.FOR_FIELD, 'exceeds the maximum',
            '({value} > {max})')
        EXCEEDS_MIN = ConditionalString("The value", FieldError.FOR_FIELD, 'exceeds the minimum',
            '({value} < {min})')
        DISALLOWED_VALUE = ConditionalString("The field", FieldError.FIELD, 'value', FieldError.VALUE, 'is not allowed')
        DISALLOWED_KEY = ConditionalString('The field', FieldError.FIELD, 'key', FieldError.KEY, 'is not allowed')
        NON_CONFIGURABLE_FIELD = ConditionalString('The field', FieldError.FIELD, 'is not configurable')
        EXPECTED_FIELD_INSTANCE = ConditionalString('The field', FieldError.FIELD, 'is not a Field instance')
        UNEXPECTED_FIELD_INSTANCE = ConditionalString('The field', FieldError.FIELD,
            'should not be a Field instance')
        # Keep for Field Value
        FIELD_ALREADY_SET = ConditionalString('The field', FieldError.FIELD, 'was already set')
        CANNOT_ADD_FIELD = ConditionalString('The field', FieldError.FIELD,
            'does not already exist and thus cannot be configured')
        CANNOT_ADD_CONFIGURABLE_FIELD = ConditionalString('Cannot add configurable field',
            FieldError.FIELD, 'to a non-configurable set')
