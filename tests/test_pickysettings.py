from pickysettings import __version__
from pickysettings import LazySettings


"""
Tests package specifications as well as certain test logic/utils that are used
throughout the testing package, most notably in regard to the temporary creation,
importing and reloading of modules.
"""


def test_version():
    assert __version__ == '0.1.0'


def test_module_reload(tmp_module, tmpdir):
    """
    Helps us to ensure that updating the content of the same file in a given
    test will have the changes reflected in LazySettings when the module due to
    proper module reloading/cache clearing.
    """
    content = """
    TEST_VARIABLE_1 = 5
    TEST_VARIABLE_3 = 10
    """

    tmp_module('app/settings/dev.py', content=content)
    settings = LazySettings('dev', base_dir='app/settings')
    assert settings.TEST_VARIABLE_1 == 5

    content2 = """
    TEST_VARIABLE_1 = 50
    TEST_VARIABLE_3 = 100
    """

    tmp_module('app/settings/dev.py', content=content2)
    settings = LazySettings('dev', base_dir='app/settings')
    assert settings.TEST_VARIABLE_1 == 50


def test_module_reload_first_func(tmp_module, tmpdir):
    """
    Helps us ensure that settings modules created off of the tmpdir for any
    given test are properly reloaded and handled independently across various
    tests.

    This has to do with the `__init__.py` problem, which is mentioned in the
    /tests/module.py file.
    """
    content = """
    TEST_VARIABLE_1 = 5
    TEST_VARIABLE_2 = 10
    """

    tmp_module('app/settings/dev.py', content=content)
    settings = LazySettings('dev', base_dir='app/settings')

    # Important to check .as_dict() instead of individual parameters to make sure
    # settings parameters are not getting included from a setting module created
    # in another test.
    assert settings.as_dict() == {
        'TEST_VARIABLE_1': 5,
        'TEST_VARIABLE_2': 10,
    }


def test_module_reload_second_func(tmp_module, tmpdir):
    """
    Helps us ensure that settings modules created off of the tmpdir for any
    given test are properly reloaded and handled independently across various
    tests.

    This has to do with the `__init__.py` problem, which is mentioned in the
    /tests/module.py file.
    """
    content = """
    TEST_VARIABLE_1 = 50
    TEST_VARIABLE_3 = 100
    """

    tmp_module('app/settings/dev.py', content=content)
    settings = LazySettings('dev', base_dir='app/settings')

    # Important to check .as_dict() instead of individual parameters to make sure
    # settings parameters are not getting included from a setting module created
    # in another test.
    assert settings.as_dict() == {
        'TEST_VARIABLE_1': 50,
        'TEST_VARIABLE_3': 100,
    }


def test_importing_from_temp_module(tmp_module):
    tmp_module('app/settings/dev.py')
    import app.settings.dev  # noqa
