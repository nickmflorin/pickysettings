import pathlib
import pytest

from pickysettings.core.fields import ConstantField


def test_converts_constants_to_fields(temp_module, test_setting):

    content = """
    import pathlib

    TEST_VARIABLE_1 = 1
    TEST_VARIABLE_2 = 30
    """

    temp_module('app/settings/dev.py', content=content)

    base_path = pathlib.PosixPath('app/settings')
    setting = test_setting('dev', base_path=base_path)
    setting.load()

    assert setting.fields.TEST_VARIABLE_1 == ConstantField(1)
    assert setting.fields.TEST_VARIABLE_2 == ConstantField(30)


def test_case_insensitive(temp_module, test_settings):

    temp_module('app/settings/dev.py', content={
        'TEST_VARIABLE_1': 'TEST',
        'TEST_VARIABLE_2': 'TEST2',
    })
    settings = test_settings('dev', base_dir='app/settings')

    assert settings.test_variable_1 == 'TEST'
    assert settings.test_variable_2 == 'TEST2'


def test_functions_ignored(temp_module, test_settings):

    content = """
    def sample_function():
        return 1

    TEST_VARIABLE_1 = 5
    TEST_VARIABLE_2 = 10
    """

    temp_module('app/settings/dev.py', content=content)
    settings = test_settings('dev', base_dir='app/settings')

    assert settings.TEST_VARIABLE_1 == 5
    assert settings.TEST_VARIABLE_2 == 10

    with pytest.raises(AttributeError):
        settings.sample_function


def test_imports_ignored(temp_module, test_settings):

    content = """
    import pathlib

    TEST_VARIABLE_1 = 1
    TEST_VARIABLE_2 = 30
    """

    temp_module('app/settings/dev.py', content=content)
    settings = test_settings('dev', base_dir='app/settings')

    assert settings.TEST_VARIABLE_1 == 1
    assert settings.TEST_VARIABLE_2 == 30
    with pytest.raises(AttributeError):
        settings.pathlib
