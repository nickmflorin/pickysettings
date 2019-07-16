import argparse
from dataclasses import dataclass, field, fields, replace, InitVar
# from dacite import from_dict
from enum import Enum
import os
import typing
import warnings

from termx.library import ensure_iterable

from .fields import SetField
from .fields.base import FieldABC
from .setting import Setting
from .utils import FieldStorable

from .exceptions import (
    InvalidSettingFile, SettingsLoadError, EnvVarNotFound, EnvVarsNotFound,
    SettingsNotConfigured, FieldConfigurationError)


DEFAULT_CMD_LINE_ARGS = ['--pickysettings']


class ValidationModes(Enum):

    NONE = 1
    STRICT = 2

    @property
    def strict(self):
        return self.name == 'STRICT'

    @classmethod
    def from_string(cls, value):
        if value is None:
            return ValidationModes.NONE
        try:
            return getattr(cls, value.upper())
        except AttributeError:
            raise ValueError('Invalid validation mode %s.' % value)


@dataclass
class SettingsOptions:

    debug: bool = False
    validation: ValidationModes = ValidationModes.STRICT
    command_line_args: typing.Union[typing.List[str]] = field(default_factory=tuple)
    env_keys: typing.Union[typing.List[str], str] = field(default_factory=tuple)

    def __post_init__(self):

        if not isinstance(self.validation, ValidationModes):
            self.validation = ValidationModes.from_string(self.validation)

        self.env_keys = ensure_iterable(self.env_keys,
            coercion=tuple, force_coerce=True)
        self.command_line_args = ensure_iterable(self.command_line_args,
            coercion=tuple, force_coerce=True)

        for cli_arg in DEFAULT_CMD_LINE_ARGS:
            if cli_arg not in self.command_line_args:
                self.command_line_args = self.command_line_args + (cli_arg, )

    # @classmethod
    # def from_dict(cls, *args, **kwargs):
    #     return from_dict(data_class=cls, data=dict(*args, **kwargs))


class LazySettings(FieldStorable):
    """
    Adopted from simple_settings module
    < https://github.com/drgarcia1986/simple-settings >

    Responsible for loading the settings files from the locations specified
    either by environment variables, command line args or arguments passed
    directly into the settings init.

    Settings files are designated by strings that reference the file that we
    are loading.  These strings are wrapped in the `Setting` object.

    [!] IMPORTANT:
    -------------
    If we stick with PosixPaths, we might have to choose between PurePosixPath
    and PureWindowsPath depending on the OS.

    The only reason we use PosixPath vs. Path is that we need the OS operations:
        - .absolute()
        - .exists()

    Otherwise, we could stick to Path since we would only need path manipulation.
    If we can find a way to use other logic for .absolute() and .exists(), it might
    be safer than potentially having to detect OS and adjust logic.
    """

    def __init__(self, *settings, base_dir=None, **kwargs):
        """
        Initializes the settings with the optionally passed in settings list.
        Requires either settings passed in via the `settings` argument, settings
        specified as an ENV variable or settings specified as a command line
        argument, otherwise SettingsNotConfigured will be raised.

        The actual setting files are not loaded until either an attribute on the
        LazySettings instance is accessed or a LazySettings instance is configured
        with overrides.
        """
        self._settings = list(settings)
        self._options = SettingsOptions(**kwargs)
        self._base_dir = base_dir

        self._base_path = None
        self._initialized = False
        self.settings = []

        super(LazySettings, self).__init__()

    def __getitem__(self, key):
        """
        For value acceses by attribute or key, we want to return the value of
        the field itself, not the field object.
        """
        self._setup()  # Force Setup if Not Initialized
        value = super(LazySettings, self).__getitem__(key)
        return value.value

    @property
    def command_line_args(self):
        return [
            '--%s' % ag if not ag.startswith('--') else ag
            for ag in self._options.command_line_args
        ]

    @property
    def arg_parser(self):
        parser = argparse.ArgumentParser()
        for cli_arg in self.command_line_args:
            parser.add_argument(cli_arg)
        return parser

    def update(self, setting):
        """
        Sets the initial settings for the given setting object after it has loaded
        the values from its associated file.

        This is meant to be a PRIVATE method.

        This is only called once per setting, on initialization.  Any changes
        to the values contained in the LazySetting instance after initialization
        must be updated through the configure() method.
        """
        if setting._stored:
            raise RuntimeError('Can only update instance with each setting file once.')

        for k, v in setting.items():
            self.__setitem__(k, v)
        setting._stored = True

    def as_dict(self):
        self._setup()
        return super(LazySettings, self).as_dict()

    def configure(self, *args, **kwargs):
        """
        After LazySettings are populated initially, using the .update() method,
        the only way to make changes to the settings is to use the .configure()
        method.

        This method is used primarily for configuring the system settings loaded
        on initialization with overridden settings provided by the user.

        Since this is used for updating the settings by the user, we do not allow
        (1) Configuring fields that are not already present
        (2) Configuring fields that are constants (not Field instances)
            - Values that are not instances of Field are non-configurable by default.

        Field instances that are non-configurable will throw exceptions when
        the configure method is called.

        [!] IMPORTANT
        ------------
        We must access the raw fields, i.e. not using self[k] to get the field
        values, because we need to access the field methods and properties.
        """
        self._setup()   # Force Setup if Not Initialized

        raise FieldConfigurationError.ExpectedType(
            'test', 'not-a-dict', dict,
            ext='SetField(s) must be configured with dict instance.'
        )

        for k, v in dict(*args, **kwargs).items():

            # Do Not Allow Additional Fields to be Added to Settings
            if k not in self:
                raise FieldConfigurationError.CannotAddField(
                    field=k
                )

            field = self.__getfield__(k)

            # Do Not Allow Configuring of Constants & Check Field Configurability
            # at Top Level
            if not isinstance(field, FieldABC) or not field.configurable:
                raise FieldConfigurationError.NonConfigurableField(
                    field=k
                )

            # [x] TODO: To be more consistent, we might just want to plugin
            # the dict directly and not use the keyword arg method.
            if isinstance(field, SetField):
                if not isinstance(v, dict):
                    raise FieldConfigurationError.ExpectedType(
                        k, v, dict,
                        ext='SetField(s) must be configured with dict instance.'
                    )
                field.configure(**v)
            else:
                field.configure(v)

    def _setup(self):
        """
        Checks if the settings list was provided to LazySettings on initialization,
        and if not, retrieves the settings list based on either the ENV vars
        or command line arguments.

        After the settings file is retrieved, loads the settings stored in
        each file.
        """
        if self._initialized:
            return

        self._collect()
        self._load()
        self._initialized = True

    def _load(self):
        """
        Collects the setting values from the various methods and determines the
        absolute path associated with each value, and then the module path associated
        with the absolute path and attempts to load the settings from the file
        based on importlib's module import.

        [x] TODO:
        --------
        Organize these exceptions better.  Many should be nested under SettingFileLoadError,
        since that is the base class for any reason a settings file cannot be
        loaded.

        Raises
        ------
        SettingsNotConfigured
            If no setting specification was provided through initialization of
            LazySettings, ENV variables or command line args.

        EnvVarsNotFound
            If any of the specified ENV variables do not exist in os.environ
            and validation is strict.

        SettingsLoadError
            If there is at least one SettingFileLoadError when `strict_load` is
            True, or when there are no settings specifications that result in
            a loaded settings file when `strict_mode` is False.

        BasePathIsNotDir
            Raised if the absolute form of the specified `base_path` points to a
            file instead of a directory.

        BasePathDoesNotExist
            Raised if the absolute form of the specified `base_path` does not exist.

        [x] TODO:
        --------
        We allow (with `strict_load`) for some settings files to not load (but
        have valid paths) if at least one was loaded, should we do the same for
        invalid settings paths/specifications?
        """
        errors = []
        i = 0

        while i < len(self.settings):
            setting = self.settings[i]

            try:
                setting.load()
            except InvalidSettingFile as e:
                self.settings.remove(setting)
                errors.append(e)
                if not self._options.validation.strict:
                    warnings.warn(str(e))
            else:
                self.update(setting)
                i += 1

        if errors and (self._options.validation.strict or len(self.settings) == 0):
            raise SettingsLoadError(errors, debug=self._options.debug)

    def _add(self, *settings):
        """
        Adds setting specifications to the list of settings, first creating
        Setting object instances to maintnain the settings in the specified
        file.

        [x] TODO:
        --------
        Should we raise an exception if the same setting file is loaded/included
        multiple times?  We could check if setting.get_absolute_path() hasn't
        already been referenced, but that will cause errors to be thrown here
        instead of in the _load() method.
        """
        for value in settings:
            if value not in [setting._settings_file for setting in self.settings]:
                setting_obj = Setting(value, base_dir=self._base_dir)
                self.settings.append(setting_obj)

    def _add_env_setting_file(self, env_key):
        try:
            setting_file = os.environ[env_key]
        except KeyError:
            raise EnvVarNotFound(env_key)
        else:
            self._add(setting_file)

    def _add_env_setting_files(self):
        """
        Adds values from ``os.environ`` corresponding to the keys set
        by the ``env_keys`` initialization parameter.
        """
        errors = []
        for env_key in self._options.env_keys:
            try:
                self._add_env_setting_file(env_key)
            except EnvVarNotFound as e:
                if not self._options.validation.strict:
                    warnings.warn(str(e))
                else:
                    errors.append(e)

        if errors and self._options.validation.strict:
            raise EnvVarsNotFound(errors)

    def _add_cli_setting_files(self):
        """
        Adds values from ``sys.argv`` corresponding to the keys set by the
        ``command_line_args`` initialization parameter.

        [x] TODO:
        --------
        Should we issue any kind of a warning if the CLI argument is not
        specified?
        """
        parsed = self.arg_parser.parse_known_args()[0]
        for ag in self.command_line_args:

            setting_file = getattr(parsed, ag[2:])
            if setting_file is not None:
                self._add(setting_file)

    def _collect(self):
        """
        Collects the settings specified by various methods, in the following
        order:

        (1) ENV Variables
        (2) Command Line Args
        (3) Initialization of LazySettings

        Variables defined in settings files included at the command line should
        override those in settings files defined as ENV variables, which should
        in turn be overridden by settings files defined on initialization.

        Raises
        ------
        EnvVarsNotFound
            If any of the specified ENV variables do not exist in os.environ
            and validation is strict.

        [x] TODO:
        --------
        Potentially adjust logic based on multiple different severity levels
        for validation.

        We should have a system for warning or raising exceptions if duplicate
        settings files are used.

        We could go off of just the `settings_file` value, but you can
        still specify the same file twice with different `settings_file`
        values (we would have to use the absolute path to compare).
        """
        self._add_env_setting_files()
        self._add_cli_setting_files()
        self._add(*self._settings)

        if len(self.settings) == 0:
            raise SettingsNotConfigured()
