from pickysettings.core.exceptions import FieldConfigurationError

from .utils import SettingsFieldDict, check_null_value
from .base import BaseField, FieldABC
from .value import ConstantField


class SetField(SettingsFieldDict, BaseField):
    """
    Field that stores a collection of Fields, whether configurable or
    non-configurable.

    Non-configurable parent SetFields prevent configuration of children fields.

    SetFields are initialized via the update() method (called on typical dict
    initialization) annd configured via the configure() method (if configurable).
    The update() method is called once, and only once, per SetField.
    """

    def __init__(self, *args, **kwargs):
        BaseField.__init__(
            self,
            optional=kwargs.pop('optional', None),
            configurable=kwargs.pop('configurable', None),
            help=kwargs.pop('help', None),
            name=kwargs.pop('name', None)
        )

        # Set Constants to Constant Fields
        for k, v in kwargs.items():
            if not isinstance(v, FieldABC):
                kwargs[k] = ConstantField(v, name=k)

        # Set Configurability of Children if Applicable
        # if self._configurable is not None:
        #     for k, field in kwargs.items():
        #         if 'configurable' not in v:
        #             kwargs[k].configurable = self._configurable

        # Assign Names to Children
        for k, v in kwargs.items():
            if isinstance(v, FieldABC):
                v._name = k

        SettingsFieldDict.__init__(self, *args, **kwargs)

    class Meta:
        options = ('help', 'name', 'optional', 'configurable')
        defaults = (
            ('help', None),
            ('name', None),
            ('optional', None),
            ('configurable', None)
        )

    @property
    def optional(self):
        """
        Sets, as a whole, are only optional if EVERY field in the set is
        optional, otherwise, any required fields must be specified.

        [x] TODO:
        --------
        We might want to follow a similar paradigm as the configurable property,
        and set the children's value of optional based on the parent's value
        of optional.
        """
        return all([v.optional for k, v in self.items()])

    @property
    def configurable(self):
        """
        If not explicitly speceified, a SetField is configurable if and only if
        if has a child that is configurable.

        [x] TODO:
        --------
        Make it so that the value of the parent configurability sets the configurability
        of the children, and raise an exceeption if there is a conflict.
        """
        if self._configurable is None:
            return any([v.configurable for k, v in self.items()])
        return self._configurable

    @check_null_value
    def _validate(self, value):
        """
        Value passed in will be a dictionary with each key corresponding to
        a field in the set.  They should be case insensitive.
        """
        return value

    def __setitem__(self, key, value):
        """
        Sets a child sub field of the SetField, all value(s) must be instances
        of Field.

        If the configurability of the parent SetField is set (i.e. not None)
        and it conflicts with the configurability of a child, we have to raise
        an exception.

        [x] NOTE:
        --------
        Cannot check configurability here because __setitem__ gets called on
        initial update as well as on configure.
        """
        if not isinstance(value, FieldABC):
            raise FieldConfigurationError.ExpectedFieldInstance()

        if self._configurable is not None:
            if value.configurable and not self._configurable:
                raise FieldConfigurationError.CannotAddConfigurableField(field=key)

        value = self._validate(value)
        super(SetField, self).__setitem__(self.__keytransform__(key), value)

    def __addfields__(self, **fields):
        """
        Method that is not supposed to be used outside of the configuration of
        system settings.

        Adds fields to the SetField after it is first initialized.  The reasoning
        is that after the SetField is initialized, the only way to make changes
        is to configure it, which is not what we want to do.

        This is useful when we have to add fields that have values that depend
        on fields already initialized:

            INSTAGRAM = fields.SetField(
                URLS=fields.SetField(
                    HOME='https://www.instagram.com/',
                    configurable=False,
                ),
            )

            HEADERS = fields.PersistentDictField({
                'Referer': INSTAGRAM.urls.home,
                "User-Agent": USERAGENT,
            })

            INSTAGRAM.__addfields__(HEADERS=HEADERES)
        """
        for k, v in fields.items():
            if k in self:
                raise FieldConfigurationError.FieldAlreadySet(k)

            self.__setitem__(k, v)

    def configure(self, *args, **kwargs):
        """
        Overrides the fields that belong to the SetField.

        (1) Cannot add fields that are not already present.
            - This would mean the addition of configuration settings instead of
              the configuring of existing settings.

        (2) Do Not Allow Configuration w/ Fields
            - Initializing the SetField requires the values to be Field instances
              or constants (converted to ConstantField(s)), whereas configuring
              requires constant values specified in a dict.

              >>> field.configure({'colors': {'apple': 'red'}})

        (3) Child fields being overridden must be configurable, as well as the
            parent SetField (self).
        """

        # Either the LazySettings object, or the parent SetField container should
        # be checking configurability of children fields before configuring.
        # However, if we configure by settings.<field_name>.configure(), we still
        # need this check.
        if not self.configurable:
            raise FieldConfigurationError.NonConfigurableField(
                field=self.name,
            )

        for k, v in dict(*args, **kwargs).items():
            # (1) Cannot add fields that are not already present.
            if k not in self:
                raise FieldConfigurationError.CannotAddField(field=k)

            field = self.__getfield__(k)
            assert isinstance(field, FieldABC)

            # (2) Do Not Allow Configuration w/ Fields - Only on Initialization
            if isinstance(v, FieldABC):
                raise FieldConfigurationError.UnexpectedFieldInstance(field=k)

            # (3) Child fields being overridden must be configurable
            if not field.configurable:
                raise FieldConfigurationError.NonConfigurableField(field=k)

            field.configure(v)

    def update(self, *args, **kwargs):
        """
        Sets the fields that belong to the SetField.  This is only done once,
        on initialization.  Updating of the SetField afterwards must be done
        through the configure method.

        Updating the SetField requires the values to be Field instances, whereas
        configuring requires dict instances.
        """
        for k, v in dict(*args, **kwargs).items():
            if k in self:
                raise FieldConfigurationError.FieldAlreadySet(field=k)

            if not isinstance(v, FieldABC):
                v = ConstantField(v)
            self.__setitem__(k, v)


FieldABC.register(SetField)
