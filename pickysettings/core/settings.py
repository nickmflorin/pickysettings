import pathlib

from .fields import SetField
from .fields.base import FieldABC

import os
import sys
import warnings

from termx.library import ensure_iterable

from .setting import Setting
from .utils import FieldStorable
from .exceptions import (
    SettingsLoadError, SettingFileLoadError, SettingsNotConfigured,
    InvalidSettingsDir, MissingSettingsDir, MissingEnvironmentKeys,
    configuration as config_exceptions)


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

    def __init__(self, *settings, base_dir=None, env_keys=None,
            command_line_args='--pickysettings', debug=False, strict_load=True):
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
        self._debug = debug
        self._strict_load = strict_load
        self._base_dir = base_dir

        self._base_path = None
        self._initialized = False
        self.settings = []

        self._env_keys = ()
        if env_keys:
            self._env_keys = ensure_iterable(env_keys, coercion=tuple, force_coerce=True)
        self._command_line_args = ensure_iterable(command_line_args, coercion=tuple, force_coerce=True)

        super(LazySettings, self).__init__()

    @property
    def base_path(self):
        """
        [x] NOTE:
        --------
        We want to use pathlib.PosixPath instances so that we can check if the
        directory exists, is a file, etc.
        """
        if not self._base_path:
            if self._base_dir:
                self._base_path = pathlib.PosixPath(self._base_dir)

                absolute_base_path = self._base_path.absolute()
                if absolute_base_path.is_file():
                    raise InvalidSettingsDir(absolute_base_path)

                if not absolute_base_path.exists():
                    raise MissingSettingsDir(absolute_base_path)

        return self._base_path

    def __getitem__(self, key):
        """
        For value acceses by attribute or key, we want to return the value of
        the field itself, not the field object.
        """
        self._setup()  # Force Setup if Not Initialized
        value = super(LazySettings, self).__getitem__(key)
        return value.value

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

        self._load()
        self._initialized = True

    def _load(self):
        """
        Collects the setting values from the various methods and determines the
        absolute path associated with each value, and then the module path associated
        with the absolute path and attempts to load the settings from the file
        based on importlib's module import.

        Raises
        ------
        SettingsNotConfigured
            If no setting specification was provided through initialization of
            LazySettings, ENV variables or command line args.
        InvalidSettingsFile
            If there is a provided setting specification that points to a file
            path that is not a file or has multiple extensions.
        SettingsFileDoesNotExist
            If there is a provided setting specification that points to a file
            that does not exist.
        UnsupportedFileType
            If there is a provided setting specification that points to a file
            with an unsupported file extension.
        UnknownFileType
            If there is a provided setting specification that points to a file
            with an unknown file extension.
        InvalidSettingsDir
            If the base_path is specified but points to a file instead of a
            directory.
        SettingDirDoesNotExist
            If the base_path is specified but does not exist.
        SettingFileLoadError
            If there is a provided setting specification that points to an existing
            and file settings file, but the file cannot be imported.
        SettingsLoadError
            If there is at least one SettingFileLoadError when `strict_load` is
            True, or when there are no settings specifications that result in
            a loaded settings file when `strict_mode` is False.

        [x] TODO:
        --------
        We allow (with `strict_load`) for some settings files to not load (but
        have valid paths) if at least one was loaded, should we do the same for
        invalid settings paths/specifications?
        """
        self._collect()

        errors = []

        invalid_settings = []
        for setting in self.settings:
            try:
                setting.load()
            except SettingFileLoadError as e:
                errors.append(e)
                invalid_settings.append(setting)
            else:
                self.update(setting)

        for setting in invalid_settings:
            self.settings.remove(setting)

        if errors:
            if self._strict_load or len(self.settings) == 0:
                raise SettingsLoadError(errors, debug=self._debug)
            else:
                exc = SettingsLoadError(errors)
                warnings.warn(str(exc))

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

    def _add_setting(self, value):
        """
        [x] TODO:
        --------
        Should we raise an exception if the same setting file is loaded/included
        multiple times?  We could check if setting.get_absolute_path() hasn't
        already been referenced, but that will cause errors to be thrown here
        instead of in the _load() method.
        """
        if value not in [setting.value for setting in self.settings]:
            setting_obj = Setting(value, base_path=self.base_path)
            self.settings.append(setting_obj)

    def _add_settings(self, settings):
        """
        Adds setting specifications to the list of settings, first creating
        Setting object instances to maintnain the settings in the specified
        file.
        """
        for value in settings:
            self._add_setting(value)

    def _collect(self):
        """
        Collects the settings specified by various methods, in the following
        order:

        (1) ENV Variables
        (2) Command Line Args
        (3) Initialization of LazySettings

        The desired effect is that setting specified from ENV variables will
        always be overriddenn by settings specified by command line arguments
        which will always be overriddenn by settings specified on initialization.
        """
        settings = self._get_specifications_from_environ()
        if settings:
            self._add_settings(settings)

        settings = self._get_specifications_from_cmd_line()
        if settings:
            self._add_settings(settings)

        self._add_settings(self._settings)

        if len(self.settings) == 0:
            raise SettingsNotConfigured()

    def _get_specifications_from_environ(self):
        """
        Returns any setting specifications set by environment variables defined
        in the initialization.  Raises MissingEnvironmentKeys if any of the
        specified ENV variable do not exist.

        [x] TODO:
        --------
        Determine if we want to allow the use of multiple ENV variables versus
        a single ENV variable.
        """
        settings_files = []
        missing_env_keys = []
        for env_key in self._env_keys:
            if env_key in os.environ:
                settings_files.append(os.environ[env_key])
            else:
                missing_env_keys.append(env_key)

        if len(missing_env_keys) and self._strict_load:
            raise MissingEnvironmentKeys(missing_env_keys)

        return settings_files

    def _get_specifications_from_cmd_line(self):
        for arg in sys.argv[1:]:
            for lib_arg in self._command_line_args:
                if arg.startswith(lib_arg):
                    try:
                        return arg.split('=')[1]
                    except IndexError:
                        return

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

        raise config_exceptions.FieldConfigurationError.ExpectedType(
            'test', 'not-a-dict', dict,
            ext='SetField(s) must be configured with dict instance.'
        )

        for k, v in dict(*args, **kwargs).items():

            # Do Not Allow Additional Fields to be Added to Settings
            if k not in self:
                raise config_exceptions.FieldConfigurationError.CannotAddField(
                    field=k
                )

            field = self.__getfield__(k)

            # Do Not Allow Configuring of Constants & Check Field Configurability
            # at Top Level
            if not isinstance(field, FieldABC) or not field.configurable:
                raise config_exceptions.FieldConfigurationError.NonConfigurableField(
                    field=k
                )

            # [x] TODO: To be more consistent, we might just want to plugin
            # the dict directly and not use the keyword arg method.
            if isinstance(field, SetField):
                if not isinstance(v, dict):
                    raise config_exceptions.FieldConfigurationError.ExpectedType(
                        k, v, dict,
                        ext='SetField(s) must be configured with dict instance.'
                    )
                field.configure(**v)
            else:
                field.configure(v)
