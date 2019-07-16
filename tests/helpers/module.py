import importlib
import pathlib
import sys
import textwrap

from .decorators import no_absolute_path, require_absolute_path, is_numeric


class module(object):

    def __init__(self, tmpdir, path, content=None, invalid=False):
        self.tmpdir = tmpdir

        self._path = path
        # This check might not be necessary anymore since we can specify relative
        # to tmpdir?
        if self._path.is_absolute():
            raise ValueError('Path cannot be absolute.')

        self._content = content
        self._invalid = invalid

    @property
    def tmppath(self):
        return pathlib.PosixPath(self.tmpdir)

    @property
    def content(self):
        if self._content:
            if isinstance(self._content, dict):
                return self._create_variable_content(**self._content)
            else:
                return textwrap.dedent(self._content)

    def create(self):
        """
        Creates a module at the given path by iteratively creating directories
        with an __init__.py for each part in the path.  If the last part of the
        path is a file, the file will be created with the `content` specified
        on __init__.
        """
        path_parts = self._path.parts
        if self._path.suffix:
            path_parts = self._path.parent.parts

        module_path = self.tmppath
        for name in path_parts:
            module_path = self.add_submodule(module_path, name)

        if self._path.suffix:
            return self.add_file(module_path, self._path.name)
        return module_path

    def reload(self):
        """
        When we update or add modules to the tmp_modules directory, we have to
        reload the tmp_modules module, otherwise the updates will not be reflected
        in LazySettings and new settings files added will raise import errors.

        [!] IMPORTANT: Module Reloading
        -------------
        Reloading the module file only if the file already existed does not
        seem to be working, most likely due to removing modules between tests or
        sibling modules/files not being reloaded.

        We need to invlalidate importlib module caches so that changes to
        the same module file in the same test are immediately reflected.  We
        also need to reload the module specified by the given `path`.

        (1) Create Settings from Module File with Content:

            >>> tmp_module('app/settings/dev.py', content={'KEY': 'VALUE'})
            >>> settings = LazySettings('dev', base_dir='app/settings')
            >>> settings.KEY
            >>> "VALUE"

        (2) Clear `importlib` caches and reload the module at the given `path`.

            >>> importlib.invalidate_caches()
            >>> module = importlib.import_module(module_str)
            >>> importlib.reload(module)

        (3) Create Settings from Module File with New Content:

            >>> tmp_module('app/settings/dev.py', content={'KEY': 'NEW_VALUE'})
            >>> settings = LazySettings('dev', base_dir='app/settings')
            >>> settings.KEY
            >>> "NEW_VALUE"

        [!] IMPORTANT: Intentionally Invalid Modules
        -------------
        If we are intentionally creating modules that will not be importable,
        we have to specify `invalid = True`.  Otherwise, an error will be
        raised trying to relaod the module in the test, instead of an error
        importing the module in the code.

        Additionally, we must remove the module from `sys.modules` so that
        it forces the code to reload the module:

            >>> del sys.modules[module_str]
        """

        # Path here is absolute path in tmpdir directory.
        # '/private/var/folders/.../<module>/<submodule>/<file>
        module_path = self._path.absolute().relative_to(self.tmppath)
        module_str = self._get_module_string(module_path)

        importlib.invalidate_caches()

        # Honestly not sure here if we have to reload all of the containing
        # modules as well...
        if sys.modules.get(module_str):
            # This will prevent us from having to reimport the module here,
            # since it will cause an error, but will force the actual settings
            # code to reload the module.
            del sys.modules[module_str]

            if not self._invalid:
                try:
                    module = importlib.import_module(module_str)
                except ImportError as e:
                    if self._invalid:
                        print('Intentionally Not Reloading %s with Invalid Content' % module_str)
                        return
                    raise e
                else:
                    importlib.reload(module)

    @require_absolute_path
    def add_submodule(self, path, name):
        """
        At the given path, creates a module with the provided name by creating
        a directory.

        [!] IMPORTANT: __init__.py
        -------------
        Note that we do note __init__.py files to each submodule.  This is very
        important, and if we were to add __init__.py files, we would have
        difficulty reloading the module between tests.

        More reference can be found at
        >>> http://python-notes.curiousefficiency.org/en/latest/python_concepts/import_traps.html

            "The __init__.py trap"

            "This is an all new trap added in Python 3.3 as a consequence of fixing
            the previous trap (The missing __init__.py trap).  If a subdirectory
            encountered on sys.path as part of a package import contains an
            __init__.py file, then the Python interpreter will create a single
            directory package containing only modules from that directory."

        For an example/use case of how this is problematic, consider the two
        test tmp directories:

        test_func1()
        >>> `/private/var/.../test_func1/app/settings/dev.py`

        test_func2()
        >>> `/private/var/.../test_func2/app/settings/dev.py`

        If we add `__init__.py` inside the `settings` module of each dir, importing
        the module located at `app.settings.dev` will always import the first
        created module, regardless of which test we are in.
        """

        # Create Folder for Module if it Does Not Exist
        module_path = path.joinpath(name)
        if not module_path.exists():
            module_path.mkdir()
        return module_path

    @require_absolute_path
    def add_file(self, path, name):
        """
        Creates a file with the associated `name` (including suffix) at the
        module located at `path`.  If `content` is specified, the content is
        written to the file.
        """
        path = path.joinpath(name)
        if not path.exists():
            path.touch()

        if self.content:
            path.write_text(self.content)

        # We should normally call the reload() method here, but this is handled
        # explicitly by the fixture instantiating the module object.
        self.reload()

        # Path here is absolute path in tmpdir directory.
        # '/private/var/folders/.../<module>/<submodule>/<file>
        return path.relative_to(self.tmppath)

    @staticmethod
    def _create_variable_content(**kwargs):
        lines = []
        for key, val in kwargs.items():
            if not is_numeric(val):
                line_val = "%s = '%s'" % (key, val)
            else:
                line_val = "%s = %s" % (key, val)
            lines.append(line_val)
        return "\n".join(lines)

    @classmethod
    @no_absolute_path
    def _get_module_string(cls, path):
        """
        For a given path, returns the module path inside of the tests module
        directory.

        >>> module_string('app/settings/dev.py')
        >>> 'tests.tmp_modules.app.settings.dev'

        [x] NOTE:
        --------
        Will currently not work for absolute paths, which we might want to enforce
        that it can work for.
        """
        if not isinstance(path, pathlib.Path):
            path = pathlib.PosixPath(path)

        if path.is_absolute():
            raise ValueError('Path cannot be absolute.')

        if path.suffix:
            path = path.with_suffix('')
        return '.'.join(path.parts)
