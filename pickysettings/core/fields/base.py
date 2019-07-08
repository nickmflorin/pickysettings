from abc import ABC, abstractmethod, abstractproperty


class FieldABC(ABC):

    @abstractproperty
    def optional(self):
        pass

    @abstractproperty
    def configurable(self):
        pass

    @abstractproperty
    def value(self):
        pass

    @abstractproperty
    def help(self):
        pass

    @abstractproperty
    def name(self):
        pass

    @abstractmethod
    def configure(self, value):
        pass

    @abstractmethod
    def _validate(self, value):
        pass

    @abstractmethod
    def __str__(self):
        pass

    def __repr__(self):
        return self.__str__()


class BaseField(object):
    """
    Abstract base field.
    """

    def __init__(self, *args, **kwargs):
        self._set_defaults(**kwargs)

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    @property
    def __dict__(self):
        return {
            'help': self.help,
            'name': self.name,
            'value': self.value,
            'configurable': self.configurable,
            'optional': self.optional
        }

    def _set_defaults(self, **kwargs):
        options = self._meta('options')

        for k, v in kwargs.items():
            if k not in options:
                raise ValueError('Invalid field option %s.' % k)

        for option in options:
            if option in kwargs:
                setattr(self, '_%s' % option, kwargs[option])
            else:
                default = self._default(option)
                setattr(self, '_%s' % option, default)

    @classmethod
    def _meta(cls, key):
        """
        Returns an attribute of the Field class's Meta data.
        """
        meta = getattr(cls, 'Meta', None)
        if not meta:
            raise NotImplementedError("Field %s must implement Meta class." % cls.__name__)
        return getattr(meta, key)

    @classmethod
    def _default(cls, key):
        """
        Returns the default value for a given field option.
        """
        defaults = cls._meta('defaults')
        if key not in [df[0] for df in defaults]:
            raise AttributeError('Field does not have default value for %s.' % key)

        def_tuple = [df for df in defaults if df[0] == key]
        return def_tuple[0][1]

    @property
    def name(self):
        if self._name is None:
            return str(self)
        return self._name

    @property
    def help(self):
        return self._help
