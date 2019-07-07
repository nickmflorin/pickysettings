from termx.library import ensure_iterable

from pickysettings.core.exceptions import FieldConfigurationError

from .utils import check_null_value
from .base import FieldABC
from .value import ValueField


class SeriesField(ValueField):

    def __init__(self, default, **kwargs):
        self._values = kwargs.pop('values', {})  # Validation Parameters
        super(SeriesField, self).__init__(default, **kwargs)

    class Meta:
        options = ('help', 'name', 'optional', 'configurable')
        defaults = (
            ('help', None),
            ('name', None),
            ('optional', False),
            ('configurable', True)
        )

    def _validate_element_val(self, v):
        """
        [x] TODO:
        --------
        Differentiate between expected types of fields vs. values in the
        FieldConfigurationError instantiations.
        """
        if isinstance(v, FieldABC):
            raise FieldConfigurationError.UnexpectedFieldInstance()

        tp = self._values.get('type') or self._values.get('types')
        if tp:
            types = ensure_iterable(tp, coercion=tuple, force_coerce=True)
            if type(v) not in types:
                raise FieldConfigurationError.ExpectedType(v, *types)

        allowed = self._values.get('allowed')
        if allowed:
            if v not in allowed:
                raise FieldConfigurationError.DisallowedValue(value=v)

    @check_null_value
    def _validate(self, value):
        """
        We do not allow a ListField to store instances of other fields, that
        would be more appropriate for a SetField.
        """
        if not isinstance(value, list):
            raise FieldConfigurationError.ExpectedType(value, list)

        for v in value:
            if isinstance(v, FieldABC):
                raise FieldConfigurationError.UnexpectedFieldInstance()
            self._validate_element_val(v)
        return value


FieldABC.register(SeriesField)
