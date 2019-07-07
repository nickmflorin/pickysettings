import pytest

from pickysettings.lib.utils import paths_overlap


@pytest.mark.parametrize("paths", [
    ('Users/Desktop/Folder/Documents', 'Folder/Documents'),
    # There can be overlap if the longer path is absolute.
    ('/Users/Desktop/Folder/Documents', 'Folder/Documents'),
    ('Users/John/Desktop/Private/settings', 'Private/settings/dev.py'),
    ('Users/John/settings', 'settings/dev.py'),
    # These paths overlap since the first path is absolute and because of that
    # there the path is not relative to the base.
    ('/Users/Desktop/Folder/Documents', 'Users/Desktop/Folder/Documents'),
])
def test_overlaps(paths):
    overlap = paths_overlap(*paths)
    assert overlap is True


@pytest.mark.parametrize("paths", [
    # There should never be overlap if both paths are absolute.  The only way
    # that the paths would have common parts would be if they were the same path,
    # in which case an error would be raised (since they are relative).
    ('/Users/Desktop/Folder/Documents', '/Folder/Documents'),
    # There should never be overlap if the shorter path is absolute.
    ('Users/Desktop/Folder/Documents', '/Folder/Documents'),
    # Same Length without Same Path Should Return False
    ('Users/Desktop/Folder/Documents', 'repos/github/myrepo/src'),
    ('Users/Desktop/Folder/Documents', 'Users/Desktop/Folder/Data'),
    ('Users/John/settings', 'dev.py'),
    ('Users/John/Desktop/Private/settings', '/Private/settings/dev.py'),
    ('/Users/John/Desktop/Private/settings', '/Private/settings/dev.py'),
])
def test_does_not_overlap(paths):
    overlap = paths_overlap(*paths)
    assert overlap is False


@pytest.mark.parametrize("paths", [
    # Same Length and Same Paths Should Raise Error Since Paths Relative
    ('Users/Desktop/Folder/Documents', 'Users/Desktop/Folder/Documents'),
])
def test_overlap_raises(paths):
    # Same Length and Same Paths Should Raise Error Since Paths Relative
    with pytest.raises(ValueError):
        paths_overlap(*paths)
