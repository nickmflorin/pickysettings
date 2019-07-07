
class Store(dict):

    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    def __keytransform__(self, key):
        return key.upper()

    def __getitem__(self, key):
        key = self.__keytransform__(key)
        try:
            return super(Store, self).__getitem__(key)
        except KeyError:
            raise AttributeError('You did not set {} setting'.format(key))

    def __getattr__(self, key):
        return self.__getitem__(key)

    def __setitem__(self, key, value):
        super(Store, self).__setitem__(self.__keytransform__(key), value)

    def __contains__(self, key):
        key = self.__keytransform__(key)
        return super(Store, self).__contains__(key)

    def __delitem__(self, key):
        raise AttributeError('Operation Not Permitted')


class Storable(object):

    def __init__(self):
        self._store = Store()

    def update(self, *args, **kwargs):
        self._store.update(*args, **kwargs)

    def copy(self):
        return self._store.copy()

    def clear(self):
        return self._store.clear()

    def items(self):
        return self._store.items()

    def __getitem__(self, key):
        return self._store.__getitem__(key)

    def __getattr__(self, key):
        try:
            return self.__getitem__(key)
        except AttributeError:
            try:
                return self.__getattribute__(key)
            except AttributeError:
                raise AttributeError('You did not set {} setting'.format(key))

    def __setitem__(self, key, value):
        return self._store.__setitem__(key, value)

    def __contains__(self, key):
        return self._store.__contains__(key)
