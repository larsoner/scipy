
import sys as _sys
from keyword import iskeyword as _iskeyword
from collections import _tuplegetter


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


# Note: This code is adapted from CPython:Lib/collections/__init__.py
def make_tuple_bunch(typename, field_names, extra_field_names=None,
                     module=None):
    if extra_field_names is None:
        extra_field_names = []
    _validate_names(typename, field_names, extra_field_names)

    # Validate the field names.  At the user's option, either generate an error
    # message or automatically replace the field name with a valid name.
    if isinstance(field_names, str):
        field_names = field_names.replace(',', ' ').split()
    field_names = list(map(str, field_names))
    typename = _sys.intern(str(typename))

    for name in [typename] + field_names:
        if type(name) is not str:
            raise TypeError('Type names and field names must be strings')
        if not name.isidentifier():
            raise ValueError('Type names and field names must be valid '
                             f'identifiers: {name!r}')
        if _iskeyword(name):
            raise ValueError('Type names and field names cannot be a '
                             f'keyword: {name!r}')

    seen = set()
    for name in field_names:
        if name.startswith('_'):
            raise ValueError('Field names cannot start with an underscore: '
                             f'{name!r}')
        if name in seen:
            raise ValueError(f'Encountered duplicate field name: {name!r}')
        seen.add(name)

    # Variables used in the methods and docstrings
    field_names = tuple(map(_sys.intern, field_names))
    extra_field_names = tuple(map(_sys.intern, extra_field_names))
    # rstrip necessary for singleton tuple
    arg_list = repr(field_names).replace("'", "")[1:-1].rstrip(',')
    full_list = arg_list
    repr_fmt = '('
    repr_fmt += ', '.join(f'{name}=%({name})r' for name in field_names)
    if len(extra_field_names):
        repr_fmt += ', '
        repr_fmt += ', '.join(f'{name}=%({name})s'
                              for name in extra_field_names)
        full_list += ', '
        full_list += repr(extra_field_names).replace("'", "")[1:-1]
    repr_fmt += ')'
    tuple_new = tuple.__new__
    _dict, _tuple, _zip = dict, tuple, zip

    # Create all the named tuple methods to be added to the class namespace

    s = f"""\
def __new__(_cls, {arg_list}, **extra_fields):
    out = _tuple_new(_cls, ({arg_list},))
    for key in out._extra_fields:
        if key not in extra_fields:
            raise TypeError("missing keyword argument '%s'" % (key,))
    for key, val in extra_fields.items():
        if key not in out._extra_fields:
            raise TypeError("unexpected keyword argument '%s'" % (key,))
        out._extra_fields[key] = val
    return out
"""
    del arg_list
    namespace = {'_tuple_new': tuple_new,
                 '__builtins__': dict(setattr=setattr, set=set,
                                      TypeError=TypeError),
                 '__name__': f'namedtuple_{typename}'}
    exec(s, namespace)
    __new__ = namespace['__new__']
    __new__.__doc__ = f'Create new instance of {typename}({full_list})'

    def __repr__(self):
        'Return a nicely formatted representation string'
        return self.__class__.__name__ + repr_fmt % self._asdict()

    def _asdict(self):
        'Return a new dict which maps field names to their values.'
        out = _dict(_zip(self._fields, self))
        out.update(self._extra_fields)
        return out

    def __getnewargs_ex__(self):
        'Return self as a plain tuple.  Used by copy and pickle.'
        return _tuple(self), self._extra_fields

    # Modify function metadata to help with introspection and debugging
    for method in (__new__, __repr__, _asdict, __getnewargs_ex__):
        method.__qualname__ = f'{typename}.{method.__name__}'

    # Build-up the class namespace dictionary
    # and use type() to build the result class
    class_namespace = {
        '__doc__': f'{typename}({full_list})',
        '__slots__': (),
        '_fields': field_names,
        '__new__': __new__,
        '__repr__': __repr__,
        '_asdict': _asdict,
        '_extra_fields': {k: None for k in extra_field_names},
        '__getnewargs_ex__': __getnewargs_ex__,
    }
    for index, name in enumerate(field_names):
        doc = _sys.intern(f'Alias for field number {index}')
        class_namespace[name] = _tuplegetter(index, doc)
    for name in extra_field_names:
        doc = _sys.intern(f'Alias for name {name}')

        def _get(self, name=name):
            return self._extra_fields[name]
        class_namespace[name] = property(_get)

    result = type(typename, (tuple,), class_namespace)

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
