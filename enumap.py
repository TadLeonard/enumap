import enum

from collections import namedtuple, OrderedDict
from itertools import zip_longest


__version__ = "1.2.3"


class Enumap(enum.Enum):
    """An Enum that maps data to its ordered, named members.
    Produces OrderedDicts and namedtuples while ensuring that the
    keys/fields match the names of the Enum members."""

    @classmethod
    def names(cls):
        try:
            names = cls.__names
        except AttributeError:
            names = cls.__names = tuple(cls.__members__)
        return names

    @classmethod
    def map(cls, *values, **named_values):
        """Returns an OrderedDict from `values` & `named_values`, whose
        keys match this Enum's members and their ordering

        >>> Fruit = Enumap("Fruit", names="apple orange papaya")
        >>> Fruit.map("heart-shaped", "spherical", papaya="ellipsoid")
        OrderedDict([('apple', 'heart-shaped'), ('orange', ...), ...])
        """
        mapping = cls._make_checked_mapping(*values, **named_values)
        return OrderedDict(((k, mapping[k]) for k in cls.names()))

    @classmethod
    def map_casted(cls, *values, **named_values):
        """Like `map`, but values are converted with the `types`
        mapping. Useful for deserializing ordered and named values.

        >>> class Order(str, Enumap):
        ...    index: int = "Order ID"
        ...    cost: Decimal = "Total pretax cost"
        ...    due_on: arrow.get = "Delivery date"
        ...
        >>> Order.map_casted("342 32342.23 2017-09-01".split())
        OrderedDict(('index', 342), ('cost', Decimal("3242.23")), ...)
        """
        mapping = cls._make_casted_mapping(*values, **named_values)
        return OrderedDict(((k, mapping[k]) for k in cls.names()))

    @classmethod
    def tuple(cls, *values, **named_values):
        """Returns a namedtuple from `values` & `named_values`, whose
        fields match this Enum's members and their ordering

        >>> Tool = Enumap("Tool", names="hammer mallet forehead")
        >>> Tool.tuple("small", "heavy", forehead="unwieldy")
        Tool_tuple(hammer='small', mallet='heavy', forehead='unwieldy')
        """
        tuple_class = cls.tuple_class()
        try:
            return tuple_class(*values, **named_values)
        except TypeError:
            mapping = cls._make_checked_mapping(*values, **named_values)
            return tuple_class(**mapping)

    @classmethod
    def tuple_casted(cls, *values, **named_values):
        """Like `tuple`, but values are converted with the `types`
        mapping. Useful for deserializing ordered and named values."""
        mapping = cls._make_casted_mapping(*values, **named_values)
        return cls.tuple_class()(**mapping)

    @classmethod
    def tuple_class(cls):
        """`namedtuple` class with fields that match this Enum's
        members and their ordering"""
        try:
            tuple_class = cls.__tuple_class
        except AttributeError:
            tuple_class = namedtuple(cls.__name__ + "_tuple", cls.names())
            cls.__tuple_class = tuple_class
        return tuple_class

    @classmethod
    def set_types(cls, *types, **named_types):
        """Set `types` mapping for `map/tuple_casted` methods.

        >>> Pastry = Enumap("Pastry", names="croissant donut muffin")
        >>> Pastry.set_types(int, int, int, donut=float)
        >>> Pastry.types()  # donut kwarg overrides donut arg
        {'croissant': int, 'donut': float, 'muffin': int}
        """
        # type mappings are allowed to be a subset of the member keys
        # in other words, not all members have to have a type
        sparse_types = SparseEnumap("temporary_types", cls.names())
        sparse_type_map = sparse_types.map(*types, **named_types)
        non_null_types = {k: v for k, v in sparse_type_map.items()
                          if v is not None}
        type_subset = Enumap(f"{cls.__name__}_types",
                             tuple(non_null_types.keys()))
        cls.__member_types = type_subset.map(*types, **named_types)

    @classmethod
    def types(cls):
        """Mapping like `{member_name: callable}` for `map/tuple_casted`.
        This can either come from type annotations or `set_types`."""
        try:
            return cls.__member_types
        except AttributeError:
            types = dict(getattr(cls, "__annotations__", {}))
            cls.__member_types = types
            return cls.__member_types

    @classmethod
    def _make_checked_mapping(cls, *values, **named_values):
        """Generate key-value pairs where keys are strictly the names
        of the members of this Enum. Raises `KeyError` for both
        missing and invalid keys."""
        names = cls.names()
        mapping = dict(zip(names, values), **named_values)
        if set(mapping) == set(names) and len(values) <= len(names):
            return mapping
        else:
            cls._raise_invalid_args(values, mapping, names)

    @classmethod
    def _make_casted_mapping(cls, *values, **named_values):
        """Like `_make_checked_mapping`, but values are casted based
        on the `types()` mapping"""
        mapping = cls._make_checked_mapping(*values, **named_values)
        types = cls.types()
        mapping.update(((k, types[k](mapping[k])) for k, v in types.items()))
        return mapping

    @classmethod
    def _raise_invalid_args(cls, values, mapping, names):
        missing = (set(names) - set(mapping)) or {}
        invalid = (set(mapping) - set(names)) or {}
        if len(values) > len(names):
            n_args = len(values)
            n_expected = len(names)
            raise KeyError(
                f"{cls.__name__} requires keys {names}; "
                f"expected {n_expected} arguments, got {n_args}")
        else:
            raise KeyError(
                f"{cls.__name__} requires keys {names}; "
                f"missing keys {missing}; invalid keys {invalid}")


class default(enum.auto):
    """A subclass of enum.auto that

    1. behaves as a unqiue enum member because enum members that aren't unique
       effectively become aliases
    2. gives the user a way of signaling that an enum value should be used as
       a default in the collections created by SparseEnumap.map() or .tuple()

    Sample usage:

        >>> class Pets(SparseEnumap):
        ...    dogs: int = default(3)
        ...    cats: int = default(44)
        ...    squirrels: float = 3  # this isn't a default at all

        >>> Pets.tuple()
        Pets_tuple(dogs=3, cats=44, squirrels=None)
    """

    def __init__(self, default_value=None):
        self._value = (enum.auto.value, default_value)

    @property
    def value(self):
        return self

    @value.setter
    def value(self, new_value):
        actual_default = self._value[-1]
        self._value = (new_value, actual_default)

    @property
    def default(self):
        return self._value[1]


def _iter_member_defaults(members):
    """Iterates through Enum members and teases out the default value
    the user selected with `default(<user's special value>)` from the
    `default` object.
    """
    for k, v in members.items():
        if isinstance(v.value, default):
            yield k, v.value.default

        # By not yielding k, v for non-default() objects, we avoid using
        # things like auto() as defaults in our .tuple()/.map() collections.
        # This makes it explicit when a user is using an enum value
        # as a default while ALSO allowing SparseEnumaps to adhere to the
        # rules of Enums. Each value of an Enum must be unique, and those that
        # aren't are basically just aliases


class SparseEnumap(Enumap):
    """A less strict Enumap that provides default values
    for unspecified keys. Invalid keys are still prohibited."""

    @classmethod
    def set_defaults(cls, *values, **named_values):
        cls.__member_defaults = cls.map(*values, **named_values)

    @classmethod
    def defaults(cls):
        try:
            return cls.__member_defaults
        except AttributeError:
            members = cls.__members__
            member_defaults = dict(_iter_member_defaults(members))
            cls.__member_defaults = member_defaults
            return cls.__member_defaults

    @classmethod
    def _make_checked_mapping(cls, *values, **named_values):
        """Generate key-value pairs where keys are strictly the names
        of the members of this Enum. Raises `KeyError` for both
        missing and invalid keys."""
        names = cls.names()
        names_set = set(names)
        defaults = cls.defaults()

        # Create a mapping which will be a subset of the final,
        # sparse mapping. As we go, record which values are present
        # in the mapping and which are missing.
        if defaults:
            mapping = dict(zip(names, values), **named_values)
            missing = names_set - set(mapping)
            mapping.update(((k, defaults[k]) for k in missing))
        else:
            mapping = dict(zip_longest(names, values), **named_values)

        # If we haven't been passed invalid keys and we haven't been
        # passed too many positional arguments, return the mapping
        if set(mapping) == names_set and len(values) <= len(names):
            return mapping
        else:
            cls._raise_invalid_args(values, mapping, names)

    @classmethod
    def _make_casted_mapping(cls, *values, **named_values):
        """Like `_make_checked_mapping`, but values are casted based
        on the `types()` mapping"""
        names = cls.names()
        names_set = set(names)
        defaults = cls.defaults()

        # Create a mapping which will be a subset of the final,
        # sparse mapping. As we go, record which values are present
        # in the mapping and which are missing.
        if defaults:
            mapping = dict(zip(names, values), **named_values)
            present = set(mapping)
            missing = names_set - present
            mapping.update(((k, defaults[k]) for k in missing))
        else:
            mapping = dict(zip(names, values), **named_values)
            present = set(mapping)
            missing = names_set - present

        # Cast the values of our mapping with the the type function
        # corresponding to their keys. We use the `missing` set of keys
        # as a guide here because we don't want to cast missing or default
        # values.
        types = cls.types()
        if types:
            present_typed = present & set(types)
            mapping.update(((k, types[k](mapping[k]))
                            for k in present_typed))

        # Handle default values to create a sparse mapping.
        # Missing values will either be filled in with what's in the
        # `defaults` mapping or with None if the user hasn't set defaults.
        temp = dict(defaults) or {}.fromkeys(names)
        temp.update(mapping)
        mapping = temp

        # If we haven't been passed invalid keys and we haven't been
        # passed too many positional arguments, return the mapping
        if not present - names_set and len(values) <= len(names):
            return mapping
        else:
            cls._raise_invalid_args(values, mapping, names)

    @classmethod
    def _raise_invalid_args(cls, values, mapping, names):
        if len(values) > len(names):
            n_args = len(values)
            n_expected = len(names)
            raise KeyError(
                f"{cls.__name__} requires keys {names}; "
                f"expected {n_expected} arguments, got {n_args}")
        else:
            invalid = set(mapping) - set(names)
            raise KeyError(f"{cls.__name__} requires keys {names}; "
                           f"invalid keys {invalid}")
