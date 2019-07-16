class PickySettingsError(Exception):
    pass


"""
NOMENCLATURE
------------

LazySettings Stages:

    (1) Composition:
            The initialization of the LazySettings object and collection of
            settings file specifications (i.e. the string pointing to the file,
            not the file itself) from ``os.environ``, command line arguments and
            initialization args.

    (2) Load:
            The "lazy" phase of the ``LazySettings`` instance that involves
            loading the contents from the modules specified by the settings files
            collected in the composition phase.

    (3) Configure:
            The manual phase of the ``LazySettings`` instance that involves the
            overriding of default field values through configuration methods.

"""


class ComposeError(PickySettingsError):
    """
    Abstract base exception class for exceptions raised during the "Composition"
    stage of the ``LazySettings`` instance life.

    This includes almost everything except for the actual importing of the
    settings files and validation of the fields.
    """
    pass


class LoadError(PickySettingsError):
    """
    Abstract base exception class for exceptions raised during the "Load"
    stage of the ``LazySettings`` instance life.
    """
    pass


class ConfigureError(PickySettingsError):
    """
    Abstract base exception class for exceptions raised during the "Configure"
    stage of the ``LazySettings`` instance life.
    """
    pass
