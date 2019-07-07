from termx.library import ensure_iterable

from pickysettings.core.exceptions import FieldConfigurationError

from .utils import check_null_value
from .base import FieldABC
from .series import SeriesField


class DictField(SeriesField):

    def __init__(self, default, **kwargs):
        self._keys = kwargs.pop('keys', {})  # Validation Parameters
        super(DictField, self).__init__(default, **kwargs)

    class Meta:
        options = ('help', 'name', 'optional', 'configurable')
        defaults = (
            ('help', None),
            ('name', None),
            ('optional', False),
            ('configurable', True)
        )

    def _validate_element_key(self, k):
        """
        [x] TODO:
        --------
        Differentiate between expected types of fields vs. values in the
        FieldConfigurationError instantiations.
        """
        tp = self._keys.get('type') or self._keys.get('types')
        if tp:
            types = ensure_iterable(tp, coercion=tuple, force_coerce=True)
            if not isinstance(k, types):
                raise FieldConfigurationError.ExpectedType(k, *types)

        allowed = self._keys.get('allowed')
        if allowed:
            if k not in allowed:
                raise FieldConfigurationError.DisallowedKey(key=k)

    @check_null_value
    def _validate(self, value):
        """
        We do not allow a DictField to store instances of other fields, that
        would be more appropriate for a SetField.
        """
        if not isinstance(value, dict):
            raise FieldConfigurationError.ExpectedType(value, dict)

        for k, v in value.items():
            if isinstance(v, FieldABC):
                raise FieldConfigurationError.UnexpectedFieldInstance(field=k)

            # Should this be done in configure instead?  Should we even have this?
            if k not in self.value:
                raise FieldConfigurationError.CannotAddField(field=k)

            self._validate_element_val(v)
            self._validate_element_key(k)
        return value

    def __str__(self):
        return "<%s %s>" % (self.__class__.__name__, dict(self))


FieldABC.register(DictField)
