import itertools
import random
import string
import textwrap

from .decorators import is_numeric


class FileContent(object):

    def __init__(self, *args, **kwargs):

        self._randomized = False

        self._string_content = None
        self._dict_content = None

        self._original_content = None
        if len(args) != 0:
            self._original_content = args[0]

        self._params = kwargs.get('params', [])
        self._original_params = self._params

        self._values = kwargs.get('values', [])
        self._original_values = self._values

        self.reset()

    def reset(self):
        self._randomized = False
        self._params = self._original_params[:]
        self._values = self._original_values[:]

        self._string_content = None
        self._dict_content = None
        self._content = self._original_content

        if isinstance(self._original_content, dict):
            self._dict_content = self._original_content
        else:
            self._string_content = self._original_content

    @property
    def values(self):
        if not self._randomized:
            self.randomize()
        return self._values

    @property
    def params(self):
        if not self._randomized:
            self.randomize()
        return self._params

    @property
    def content(self):
        # Is this a good idea to do?  Or treat this as a non-prop?
        if not self._randomized:
            self.randomize()
        return textwrap.dedent(self._content)

    @property
    def as_string(self):
        return self.content

    @property
    def as_dict(self):
        if not self._randomized:
            self.randomize()
        if self._dict_content is not None:
            return self._dict_content
        return {}

    @content.setter
    def content(self, value):
        if isinstance(value, dict):
            lines = []
            for key, val in value.items():
                if not is_numeric(val):
                    line_val = "%s = '%s'" % (key, val)
                else:
                    line_val = "%s = %s" % (key, val)
                lines.append(line_val)

            self._string_content = "\n".join(lines)
            self._dict_content = value
        else:
            self._string_content = value
            self._dict_content = None

        self._content = self._string_content

    @classmethod
    def random_string(cls, length=None):
        """
        Generate a random string with the combination of lowercase and
        uppercase letters.
        """
        letters = string.ascii_letters

        if not length:
            length = random.randint(5, 10)

        upper = random.choice([True, False, False])
        rand_string = ''.join(random.choice(letters) for i in range(length))
        if upper:
            return rand_string.upper()
        return rand_string.lower()

    @classmethod
    def random_int(cls):
        return random.randint(0, 1000)

    @classmethod
    def random_float(cls):
        return round(float(cls.random_int() / cls.random_int()), 3)

    @classmethod
    def random_values(cls, num_values):
        cycler = itertools.cycle([
            cls.random_string,
            cls.random_int,
            cls.random_float
        ])

        values = []
        for _ in range(num_values):
            randomizer = next(cycler)
            values.append(randomizer())
        return values

    @classmethod
    def random_params(cls, num_params):
        return [cls.random_string() for _ in range(num_params)]

    def randomize(self, **kwargs):
        """
        Generates a set of key-value pairs for creating content of a test
        module file so that the keys and values are unique for each test.

        This ensures that we are in fact not reading a previously created
        temporary module file that was not reloaded, and it also guarantees
        that we are testing different variable types.
        """
        test_cls = kwargs.get('test_cls')

        self.reset()

        if self._string_content:
            self.content = self._string_content

        elif self._dict_content:

            if test_cls:
                new_content = {}
                for k, v in self._content.items():
                    new_key = "%s_%s" % (k, test_cls.file_count)
                    new_content[new_key] = v
                self.content = new_content
            else:
                self.content = self._dict_content

        else:
            if self._params or self._values:

                if not self._values or (len(self._params) > len(self._values)):
                    # If params are set manually, make sure they are unique for
                    # each test.
                    if test_cls:
                        for i in range(len(self._params)):
                            self._params[i] = "%s_%s" % (self._params[i], test_cls.file_count)

                    self._values.extend(
                        self.random_values(len(self._params) - len(self._values)))

                elif not self._params or (len(self._values) > len(self._params)):
                    assert not self._params or len(self._values) > len(self._params)

                    self._params.extend(
                        self.random_values(len(self._values) - len(self._params)))

                assert len(self._params) == len(self._values)
                kwargs.setdefault('num_params', len(self._params))

            num_params = kwargs.get('num_params', 2)
            leftover = max(num_params - len(self._params), 0)

            self._params.extend(self.random_params(leftover))
            self._values.extend(self.random_values(leftover))

            if test_cls:
                test_cls.file_count += 1
            self.content = dict(zip(self._params, self._values))

        self._randomized = True
        return self.content
