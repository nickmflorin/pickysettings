from pickysettings.core.exceptions import ConfigFileLoadError, ConfigFileLoadingError


def test_config_file_loading_error():

    errors = [
        ConfigFileLoadError('dev.py', ValueError('Some value error.')),
        ConfigFileLoadError('base.py', ImportError('Some error during import.'))
    ]
    exc = ConfigFileLoadingError(errors, debug=False)
    print(exc)

    errors = [
        ConfigFileLoadError('dev.py', ValueError('Some value error.')),
        ConfigFileLoadError('base.py', ImportError('Some error during import.'))
    ]
    exc = ConfigFileLoadingError(errors, debug=True)
    print(exc)
