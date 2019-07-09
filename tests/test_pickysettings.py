from pickysettings import __version__


def test_version():
    assert __version__ == '0.1.0'


def test_module_reload(temp_module, test_settings):

    content = """
    TEST_VARIABLE_1 = 5
    TEST_VARIABLE_3 = 10
    """

    temp_module('app/settings/dev.py', content=content)
    settings = test_settings('dev', base_dir='app/settings')
    assert settings.TEST_VARIABLE_1 == 5

    content2 = """
    TEST_VARIABLE_1 = 50
    TEST_VARIABLE_3 = 100
    """

    temp_module('app/settings/dev.py', content=content2)
    settings = test_settings('dev', base_dir='app/settings')
    assert settings.TEST_VARIABLE_1 == 50
