import functools
import pytest


class TestSettingsBase:

    @pytest.fixture(autouse=True)
    def auto_injector_fixture(self, tests_module_path, request):

        settings_path_creator = functools.partial(self._settings_path, tests_module_path=tests_module_path)
        setattr(self, '_settings_path', settings_path_creator)

        base_path_creator = functools.partial(self._base_path, tests_module_path=tests_module_path)
        setattr(self, '_base_path', base_path_creator)

        if hasattr(self, 'settings_path'):
            setattr(self, 'settings_path', str(self._settings_path(self.settings_path)))

        if hasattr(self, 'base_path'):
            setattr(self, 'base_path', str(self._base_path(self.base_path)))

    def _settings_path(self, path, tests_module_path):
        return path

    def _base_path(self, path, tests_module_path):
        """
        Default behavior is to put the base path in the context of the test
        module.  This is not the case for the `settings_path`.
        """
        path = tests_module_path.joinpath(path)
        return path.as_posix()
