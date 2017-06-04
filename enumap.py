from collections import namedtuple, OrderedDict
from enum import Enum
from itertools import zip_longest


__version__ = "1.1.0"


class Enumap(Enum):
    """An Enum with convenience methods for mapping
    ordered values to dictionaries and namedtuples whose
    keys/fields are enforced to match the names of the Enum members"""

    @classmethod
    def names(cls):
        names = getattr(cls, "__names", None)
        if not names:
            names = tuple(cls.__members__)
            setattr(cls, "__names", names)
        return names

    @classmethod
    def map(cls, *values, **named_values):
        """Returns an OrderedDict from `values` & `named_values`, whose
        keys match this Enum's members and their ordering

        >>> Fruit = Enumap("Fruit", names="apple orange papaya")
        >>> Fruit.map("heart-shaped", "spherical", papaya="ellipsoid")
        OrderedDict(('apple', 'heart-shaped'), ('orange', ...), ...)
        """
        mapping = cls._make_checked_mapping(*values, **named_values)
        return OrderedDict(mapping)

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
        return OrderedDict(mapping)

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
        return cls.tuple_class()(**dict(mapping))

    @classmethod
    def tuple_class(cls):
        """`namedtuple` class with fields that match this Enum's
        members and their ordering"""
        t_type = getattr(cls, "__tuple_class", None)
        if not t_type:
            t_type = namedtuple(cls.__name__ + "_tuple", cls.names())
            setattr(cls, "__tuple_class", t_type)
        return t_type

    @classmethod
    def set_types(cls, *types, **named_types):
        """Set `types` mapping for `map/tuple_casted` methods.

        >>> Pastry = Enumap("Pastry", names="croissant donut muffin")
        >>> Pastry.set_types(int, int, int, donut=float)
        >>> Pastry.types()  # donut kwarg overrides donut arg
        {'croissant': int, 'donut': float, 'muffin': int}
        """
        mapping = cls._make_checked_mapping(*types, **named_types)
        setattr(cls, "__member_types", mapping)

    @classmethod
    def types(cls):
        """Mapping like `{member_name: callable}` for `map/tuple_casted`"""
        try:
            return getattr(cls, "__member_types", None) or cls.__annotations__
        except AttributeError:
            raise TypeError("{cls} has no types or type annotations")

    @classmethod
    def _make_checked_mapping(cls, *values, **named_values):
        """Generate key-value pairs where keys are strictly the names
        of the members of this Enum. Raises `KeyError` for both
        missing and invalid keys."""
        names = cls.names()
        mapping = {**dict(zip(names, values)), **named_values}
        if set(mapping) == set(names):
            return mapping
        else:
            missing = set(names) - set(mapping)
            invalid = set(mapping) - set(names)
            raise KeyError(f"{cls.__name__} requires keys {names}; "
                           f"missing keys {missing}; invalid keys {invalid}")

    @classmethod
    def _make_casted_mapping(cls, *values, **named_values):
        """Like `_make_checked_mapping`, but values are casted based
        on the `types()` mapping"""
        mapping = cls._make_checked_mapping(*values, **named_values)
        types = cls.types()
        for name, value in mapping.items():
            yield name, types[name](value)


class SparseEnumap(Enumap):
    """A less strict Enumap that provides `None` default values
    for unspecified keys"""

    @classmethod
    def _make_checked_mapping(cls, *values, **named_values):
        """Generate key-value pairs where keys are strictly the names
        of the members of this Enum. Raises `KeyError` for both
        missing and invalid keys."""
        names = cls.names()
        mapping = {**dict(zip_longest(names, values)), **named_values}
        if set(mapping) == set(names):
            return mapping
        else:
            invalid = set(mapping) - set(names)
            raise KeyError(f"{cls.__name__} requires keys {names}; "
                           f"invalid keys {invalid}")
