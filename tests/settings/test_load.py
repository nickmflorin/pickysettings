import os
import pytest

from pickysettings.core.exceptions import initialization as init_exceptions


def test_load(temp_module, test_settings):
    """
    When creating settings that we are actually going to load with importlib,
    we have to create them within the pickysettings module, so we set aside a folder
    in tests/settings for this.

    This is all handled by the self.settings_module fixture.
    """
    temp_module('app/settings/dev.py', content={
        'TEST_VARIABLE_1': 'TEST',
        'TEST_VARIABLE_2': 'TEST2',
    })
    settings = test_settings('dev', base_dir='app/settings')

    assert settings.TEST_VARIABLE_1 == 'TEST'
    assert settings.TEST_VARIABLE_2 == 'TEST2'


def test_load_multiple(temp_module, test_settings):

    content = """
    TEST_VARIABLE_1 = 1
    TEST_VARIABLE_2 = 15
    """

    content2 = """
    TEST_VARIABLE_1 = 5
    TEST_VARIABLE_3 = 10
    """

    temp_module('app/settings/dev.py', content=content)
    temp_module('app/settings/dev2.py', content=content2)

    settings = test_settings('dev', 'dev2', base_dir='app/settings')

    assert settings.TEST_VARIABLE_1 == 5
    assert settings.TEST_VARIABLE_2 == 15
    assert settings.TEST_VARIABLE_3 == 10


@pytest.mark.skip(reason="Reloading modules not working.")
def test_multiple_settings_with_invalid(temp_module, test_settings):
    """
    If LazySettings encounters an invalid/unimportable settings file during
    load, and `strict_load` is True (by default), SettingsLoadError should
    be raised when the LazySettings instance attempts to load the settings
    files.

    If `strict_load` is False, LazySettings should issue a warning for the
    invalid file but still load valid files.  If there are no valid files,
    SettingsLoadError should be raised regardless of the `strict_load`
    value.
    """
    valid_content = """
    import pathlib

    TEST_VARIABLE_1 = 1
    TEST_VARIABLE_2 = 15
    """

    invalid_content = """
    import missing_package

    TEST_VARIABLE_1 = 5
    TEST_VARIABLE_3 = 10
    """

    temp_module('app/settings/dev.py', content=valid_content)
    temp_module('app/settings/dev2.py', content=invalid_content, invalid=True)
    temp_module('app/settings/dev3.py', content=invalid_content, invalid=True)

    # Condition: `strict_load = True`,  one file invalid.
    # Expected: SettingsLoadError raised
    settings = test_settings('dev', 'dev2', base_dir='app/settings')
    with pytest.raises(init_exceptions.SettingsLoadError) as e:
        settings.TEST_VARIABLE_1

    assert (
        [err._exc.__class__ for err in e.value._errors] ==
        [ModuleNotFoundError])

    # Condition: `strict_load = False`, one file invalid.
    # Expected: SettingsLoadError not raised
    settings = test_settings('dev', 'dev2', base_dir='app/settings', strict_load=False)

    assert settings.TEST_VARIABLE_1 == 1
    assert settings.TEST_VARIABLE_2 == 15

    # Condition: `strict_load = True`, both files invalid.
    # Expected: SettingsLoadError raised (value of `strict_load` is irrelevant).
    settings = test_settings('dev3', 'dev2', base_dir='app/settings')
    with pytest.raises(init_exceptions.SettingsLoadError) as e:
        settings.TEST_VARIABLE_1

    assert (
        [err._exc.__class__ for err in e.value._errors] ==
        [ModuleNotFoundError, ModuleNotFoundError])

    # Condition: `strict_load = False`, both files invalid.
    # Expected: SettingsLoadError raised (value of `strict_load` is irrelevant).
    settings = test_settings('dev3', 'dev2', base_dir='app/settings', strict_load=False)
    with pytest.raises(init_exceptions.SettingsLoadError) as e:
        settings.TEST_VARIABLE_1

    assert (
        [err._exc.__class__ for err in e.value._errors] ==
        [ModuleNotFoundError, ModuleNotFoundError])


# @pytest.mark.skip(reason="Reloading modules not working.")
def test_invalid_import_raises(temp_module, reload_tmp_modules, test_settings):

    invalid_content = """
    import missing_package

    TEST_VARIABLE_1 = 5
    TEST_VARIABLE_3 = 10
    """

    temp_module('app/settings/dev.py', content=invalid_content, invalid=True)
    reload_tmp_modules('app', 'settings', 'dev', invalid=True)

    settings = test_settings('dev', base_dir='app/settings')
    with pytest.raises(init_exceptions.SettingsLoadError) as e:
        settings.TEST_VARIABLE_1

    assert (
        [err._exc.__class__ for err in e.value._errors] ==
        [ModuleNotFoundError])


def test_load_env_settings(temp_module, test_settings, reload_tmp_modules):

    temp_module('app/settings/dev.py', content={
        'TEST_VARIABLE_1': 'dev_TEST',
        'TEST_VARIABLE_2': 'dev_TEST2',
    })
    reload_tmp_modules('app', 'settings', 'dev')

    os.environ['TEST_FILE'] = 'dev.py'
    settings = test_settings(base_dir='app/settings', env_keys='TEST_FILE')

    assert settings.TEST_VARIABLE_1 == 'dev_TEST'
    assert settings.TEST_VARIABLE_2 == 'dev_TEST2'


# @pytest.mark.skip(reason="Reloading modules not working.")
def test_load_multiple_env_settings(TMP_MODULE_DIR, reload_tmp_modules, temp_module, test_settings):

    from pickysettings import LazySettings

    os.environ['TEST_FILE1'] = 'dev.py'
    os.environ['TEST_FILE2'] = 'dev2.py'

    temp_module('app/settings/dev.py', content={
        'TEST_VARIABLE_1': 'dev_TEST',
        'TEST_VARIABLE_2': 'dev_TEST2',
    })

    temp_module('app/settings/dev2.py', content={
        'TEST_VARIABLE_2': 'dev2_TEST2',
        'TEST_VARIABLE_3': 'dev2_TEST3',
    })

    import pathlib
    base = pathlib.PosixPath(TMP_MODULE_DIR)
    base = base.joinpath('app/settings')

    # import ipdb; ipdb.set_trace()
    # reload_tmp_modules('app', 'settings', 'dev')
    settings = LazySettings(base_dir=base, env_keys=['TEST_FILE1', 'TEST_FILE2'])

    # settings = test_settings(
    #     base_dir='app/settings',
    #     env_keys=['TEST_FILE1', 'TEST_FILE2']
    # )
    print(settings.as_dict())
    return

    assert settings.TEST_VARIABLE_1 == 'dev_TEST'
    assert settings.TEST_VARIABLE_2 == 'dev2_TEST2'
    assert settings.TEST_VARIABLE_3 == 'dev2_TEST3'


@pytest.mark.skip(reason="Reloading modules not working.")
def test_env_settings_do_not_override(temp_module, test_settings):
    """
    ENV settings should be overridden by any settings specified via
    initialization of the LazySettings object.
    """
    os.environ['TEST_FILE1'] = 'dev2.py'
    os.environ['TEST_FILE2'] = 'dev3.py'

    temp_module('app/settings/dev.py', content={
        'TEST_VARIABLE_1': 'dev_TEST',
        'TEST_VARIABLE_2': 'dev_TEST2',
    })

    temp_module('app/settings/dev2.py', content={
        'TEST_VARIABLE_2': 'dev2_TEST2',
        'TEST_VARIABLE_3': 'dev2_TEST3',
    })

    settings = test_settings('dev', base_dir='app/settings',
        env_keys=['TEST_FILE1'])

    assert settings.TEST_VARIABLE_1 == 'dev_TEST'
    assert settings.TEST_VARIABLE_2 == 'dev_TEST2'
    assert settings.TEST_VARIABLE_3 == 'dev2_TEST3'


def test_env_variables_missing(temp_module, test_settings):
    """
    If LazySettings is initialized with ENV keys and there is no file specified
    for those ENV keys, MissingEnvironmentKeys should be raised.
    """
    # temp_module('app/settings/dev.py')
    temp_module('app/settings/dev.py', content={
        'TEST_VARIABLE_1': 'dev_TEST',
        'TEST_VARIABLE_2': 'dev_TEST2',
    })
    temp_module('app/settings/test_file1.py')
    temp_module('app/settings/test_file2.py')

    settings = test_settings('dev', base_dir='app/settings')
    print(settings.TEST_VARIABLE_1)
    # settings = test_settings('dev', base_dir='app/settings',
    #     env_keys=['test_file1', 'test_file2'])

    temp_module('app/settings/dev.py', content={
        'TEST_VARIABLE_1': 'dev_TEST2',
        'TEST_VARIABLE_2': 'dev_TEST2',
    })
    settings = test_settings('dev', base_dir='app/settings')
    print(settings.TEST_VARIABLE_1)

    # with pytest.raises(init_exceptions.MissingEnvironmentKeys):
    #     settings.TEST_VARIABLE_1
