
import sys as _sys
from keyword import iskeyword as _iskeyword


class _TupleBunch:

    _fields = ()
    _extra_fields = ()

    def __init__(self, **kwds):
        # _validate_kwds isn't strictly necessary, since the code that follows
        # it will raise an exception if the names in kwds are not valid, or if
        # there is a name missing from kwds.
        # The function provides a friendlier error message.
        self._validate_kwds(kwds)
        self.__dict__['_tuple'] = tuple(kwds[name] for name in self._fields)
        for name in self._fields + self._extra_fields:
            self.__dict__[name] = kwds[name]

    def __repr__(self):
        s = (self.__class__.__name__ + '(' +
             ', '.join(f'{name}={self.__dict__[name]!r}'
                       for name in self._fields + self._extra_fields) + ')')
        return s

    def __setattr__(self, name, value):
        # Ensure that all attributes are read-only, and that new attributes
        # can't be added to the object.
        raise AttributeError("can't set attribute")

    def _validate_kwds(self, kwds):
        all_fields = self._fields + self._extra_fields
        for name in kwds:
            if name not in all_fields:
                raise TypeError(f"unexpected keyword argument '{name}'")
        for name in all_fields:
            if name not in kwds:
                raise TypeError(f"missing keyword argument '{name}'")

    # Delegate a minimal set of dunder methods to self._tuple

    def __len__(self):
        return len(self._tuple)

    def __getitem__(self, i):
        return self._tuple[i]


def _validate_names(typename, field_names, extra_field_names):
    """
    Ensure that all the given names are valid Python identifiers that
    do not start with '_'.  Also check that there are no duplicates
    among field_names + extra_field_names.
    """
    for name in [typename] + field_names + extra_field_names:
        if type(name) is not str:
            raise TypeError('typename and all field names must be strings')
        if not name.isidentifier():
            raise ValueError('typename and all field names must be valid '
                             f'identifiers: {name!r}')
        if _iskeyword(name):
            raise ValueError('typename and all field names cannot be a '
                             f'keyword: {name!r}')

    seen = set()
    for name in field_names + extra_field_names:
        if name.startswith('_'):
            raise ValueError('Field names cannot start with an underscore: '
                             f'{name!r}')
        if name in seen:
            raise ValueError(f'Duplicate field name: {name!r}')
        seen.add(name)


def make_tuple_bunch(typename, field_names, extra_field_names=None,
                     module=None):
    if extra_field_names is None:
        extra_field_names = []
    _validate_names(typename, field_names, extra_field_names)

    result = type(typename, (_TupleBunch,),
                  dict(_fields=tuple(field_names),
                       _extra_fields=tuple(extra_field_names)))

    # Note: This code to handle `module` is from the Python source code for
    # namedtuple, in Lib/collections/__init__.py
    #
    # For pickling to work, the __module__ variable needs to be set to the
    # frame where the named tuple is created.  Bypass this step in environments
    # where sys._getframe is not defined (Jython for example) or sys._getframe
    # is not defined for arguments greater than 0 (IronPython), or where the
    # user has specified a particular module.
    if module is None:
        try:
            module = _sys._getframe(1).f_globals.get('__name__', '__main__')
        except (AttributeError, ValueError):
            pass
    if module is not None:
        result.__module__ = module

    return result
