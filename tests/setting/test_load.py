import pathlib

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
