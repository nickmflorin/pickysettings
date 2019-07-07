from datetime import datetime

from termx.ext.utils import string_format_tuple

from pickysettings.core.exceptions import FieldConfigurationError

from .utils import check_null_value
from .base import BaseField, FieldABC


__all__ = (
    'ConstantField',
    'NumericField',
    'FloatField',
    'BooleanField',
    'PositiveFloatField',
    'YearField',
    'PositiveIntField',
    'IntField',
)


class ValueField(BaseField):
    """
    Abstract base class for all field objects that are not represented by
    a collection of valus.

    Provides the interface for defining methods on a field and the basic
    configuration steps for configurable fields.
    """

    def __init__(self, default, **kwargs):
        super(ValueField, self).__init__(**kwargs)
        self._value = default

    class Meta:
        """
        Configurable keyword argument of None (resulting in self._configurable = None)
        means that the configurability was not set.
        """
        options = ('help', 'name', 'optional', 'configurable')
        defaults = (
            ('help', None),
            ('name', None),
            ('optional', False),
            ('configurable', None)
        )

    @property
    def optional(self):
        return self._optional

    @property
    def configurable(self):
        """
        Returns the value of configurable if it was set, otherwise, returns the
        defeault value.

        We do not want to always set self._configurable to the default value,
        because we need to differentiate betweeen set values of configurable
        and unset values of configurable.
        """
        if self._configurable is None:
            return self._default('configurable')
        return self._configurable

    def configure(self, value):
        self.value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        if not self.configurable:
            raise FieldConfigurationError.NonConfigurableField(
                ext="Configurability should be checked by container and not field itself."
            )
        val = self._validate(val)
        self._value = val

    def __str__(self):
        if isinstance(self.value, tuple):
            return "%s" % string_format_tuple(self.value)
        return "%s" % self.value


FieldABC.register(ValueField)


class ConstantField(ValueField):
    """
    A constant field that is non configurable.  This will more often be used
    internally to create Field instances of system settings values that are
    not initialized as Field instances, which we treat as non-configurable
    constants by default.
    """

    def __init__(self, value, help=None, name=None):
        super(ConstantField, self).__init__(default=value, name=name, help=help)

    class Meta:
        options = ('help', 'name', 'optional', 'configurable')
        defaults = (
            ('help', None),
            ('name', None),
            ('optional', False),
            ('configurable', False)
        )

    def _validate(self, v):
        if isinstance(v, dict):
            raise FieldConfigurationError.UnexpectedType(v, dict,
                ext='ConstantField(s) cannot be configured with dict instances.')
        return v


class NumericField(ValueField):
    """
    Abstract base class for numeric fields where a max and a min may be
    specified.
    """

    def __init__(self, default, max=None, min=None, **kwargs):
        super(NumericField, self).__init__(default, **kwargs)
        self._max = max
        self._min = min

    @check_null_value
    def _validate(self, value):
        if self._max and value > self._max:
            raise FieldConfigurationError.ExceedsMax(value=value, max=self._max)
        if self._min and value < self._min:
            raise FieldConfigurationError.ExceedsMin(value=value, min=self._min)
        return value


class IntField(NumericField):

    @check_null_value
    def _validate(self, value):
        try:
            float(value)
        except ValueError:
            raise FieldConfigurationError.ExpectedType(value, int)
        else:
            value = int(value)
            if value != float(value):
                raise FieldConfigurationError.ExpectedType(value, int)
            return super(IntField, self).validate(value)


class FloatField(NumericField):

    @check_null_value
    def _validate(self, value):
        try:
            value = float(value)
        except ValueError:
            raise FieldConfigurationError.ExpectedType(value, float)
        else:
            return super(IntField, self).validate(value)


class PositiveIntField(IntField):

    def __init__(self, *args, **kwargs):
        kwargs['min'] = 0
        super(PositiveIntField, self).__init__(*args, **kwargs)


class YearField(IntField):

    def __init__(self, *args, **kwargs):
        kwargs['max'] = datetime.today().year

        # Nobody lives past 100, and if they do they DEFINITELY don't have an
        # Instagram account.
        kwargs['min'] = kwargs['max'] - 100
        super(YearField, self).__init__(*args, **kwargs)


class PositiveFloatField(FloatField):

    def __init__(self, *args, **kwargs):
        kwargs['min'] = 0
        super(PositiveFloatField, self).__init__(*args, **kwargs)


class BooleanField(ValueField):

    @check_null_value
    def _validate(self, value):
        if not isinstance(value, bool):
            raise FieldConfigurationError.ExpectedType(value, bool)
        return value
