import pytest

from pickysettings.core.exceptions import FieldConfigurationError
from pickysettings.core.fields import (
    DictField, SeriesField, SetField, PositiveIntField, BooleanField)


class TestSetField(object):

    configurable = SetField(
        level='INFO',
        option=BooleanField(default=False),
        configurable=True,
    )

    non_configurable = SetField(
        level='INFO',
        option=BooleanField(default=False, configurable=False),
        configurable=False,
    )

    def test_access_attribute(self):
        assert self.configurable.option is False
        assert self.configurable.OPTION is False

    def test_configure(self):
        """
        We should be able to configure configurable sub-fields of the SetField.
        """
        self.configurable.configure(option=True)
        assert self.configurable.option is True

    def test_non_configurable(self):
        """
        Exception should be raised if we try to configure non-configurable
        SetField.
        """
        with pytest.raises(FieldConfigurationError):
            self.non_configurable.configure(option=True)

    def test_configuring_new_field(self):
        pass

    def test_add_configurable_field_to_nonconfigurable_set(self):
        """
        We should not be able to add a configurable sub field to a non-configurable
        set.  If configurable is not specified on the sub-field, it should be
        defaulted to the configurability of the parent.
        """
        with pytest.raises(FieldConfigurationError):
            SetField(
                level='INFO',
                option=BooleanField(default=False, configurable=True),
                configurable=False,
            )

    def test_configure_constant(self):
        """
        Exception should be raised if we try to configure a constant field in
        a configurable SetField.
        """
        with pytest.raises(FieldConfigurationError):
            self.configurable.configure({'level': 'DEBUG'})


class TestSeriesField(object):

    configurable = SeriesField(
        ['foo', 'bar', 1, 2],
        configurable=True,
        values={
            'type': (str, int),
            'allowed': ('foo', 'bar', 'baz', 2, 1),
        }
    )

    non_configurable = SeriesField(
        ['foo', 'bar', 1, 2],
        configurable=False,
        values={
            'type': (str, int),
            'allowed': ('foo', 'bar', 'baz'),
        }
    )

    valid_series = [
        ['foo', 1, 2],
        [1, 'baz'],
    ]

    invalid_series = [
        [True, False],
        ['foo', 'bar', 'bat']
    ]

    def test_non_configurable(self):
        for series in self.valid_series:
            with pytest.raises(FieldConfigurationError):
                self.non_configurable.configure(series)

    def test_configure_valid_series(self):
        for series in self.valid_series:
            self.configurable.configure(series)
            assert self.configurable.value == series

    def test_configure_invalid_series(self):
        """
        Invalid Types in Series Should Raise FieldConfigurationError
        Disallowed Values in Series Should Raise FieldConfigurationError
        """
        for series in self.invalid_series:
            with pytest.raises(FieldConfigurationError):
                self.configurable.configure(series)


class TestDictField(object):

    configurable = DictField(
        {'foo': 1, 'bar': 2},
        configurable=True,
        keys={
            'type': str,
            'allowed': ('foo', 'bar', 'baz'),
        },
        values={
            'type': int,
            'allowed': (1, 2, 3)
        }
    )

    non_configurable = DictField(
        {'foo': 1, 'bar': 2},
        configurable=False,
        keys={
            'type': str,
            'allowed': ('foo', 'bar', 'baz'),
        },
        values={
            'type': int,
            'allowed': (1, 2, 3)
        }
    )

    def test_configurable(self):
        self.configurable.configure({'foo': 3})
        assert self.configurable.value == {'foo': 3}

    def test_nonconfigurable(self):
        with pytest.raises(FieldConfigurationError):
            self.non_configurable.configure({'foo': 3})

    def test_invalid_values(self):
        with pytest.raises(FieldConfigurationError):
            self.configurable.configure({'foo': 'apple'})

    def test_invalid_keys(self):
        with pytest.raises(FieldConfigurationError):
            self.configurable.configure({'apple': 1})
