from pickysettings.core.setting import Setting
from pickysettings.core.fields import ConstantField


def test_converts_constants_to_fields(tmp_module):

    content = """
    import pathlib

    TEST_VARIABLE_1 = 1
    TEST_VARIABLE_2 = 30
    """

    tmp_module('app/settings/dev.py', content=content)

    setting = Setting('dev', base_dir='app/settings')
    setting.load()

    assert setting.fields.TEST_VARIABLE_1 == ConstantField(1)
    assert setting.fields.TEST_VARIABLE_2 == ConstantField(30)
