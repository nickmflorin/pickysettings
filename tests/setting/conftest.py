import pytest

from pickysettings.core.setting import Setting


@pytest.fixture
def test_setting(tests_module_path):
    """
    Creates an instance of Setting with the base directory adjusted for
    the temporary settings module.
    """
    def _test_settings(*args, base_path=None):

        value = args[0]
        if hasattr(args[0], '__name__'):
            value = list(args)[1]

        base_path = tests_module_path.joinpath(base_path)
        return Setting(value, base_path=base_path)

    return _test_settings
