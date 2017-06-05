from collections import namedtuple, OrderedDict
from enum import Enum
from itertools import zip_longest


__version__ = "1.2.0"


class Enumap(Enum):
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
        try:
            return cls.tuple_class()(*values, **named_values)._asdict()
        except TypeError:
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
        mapping = cls._make_checked_mapping(*types, **named_types)
        cls.__member_types = mapping

    @classmethod
    def types(cls):
        """Mapping like `{member_name: callable}` for `map/tuple_casted`.
        This can either come from type annotations or `set_types`."""
        try:
            types = cls.__member_types
        except AttributeError:
            if hasattr(cls, "__annotations__"):
                types = cls.__member_types = cls.__annotations__
            else:
                raise TypeError("{cls} has no types or type annotations")
        return types

    @classmethod
    def _make_checked_mapping(cls, *values, **named_values):
        """Generate key-value pairs where keys are strictly the names
        of the members of this Enum. Raises `KeyError` for both
        missing and invalid keys."""
        names = cls.names()
        mapping = dict(zip(names, values), **named_values)
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
        return {k: types[k](v) for k, v in mapping.items()}


_FILL = object()  # sentinal for missing values in sparse collections


class SparseEnumap(Enumap):
    """A less strict Enumap that provides default values
    for unspecified keys. Invalid keys are still prohibited."""

    @classmethod
    def set_defaults(cls, *values, **named_values):
        mapping = cls._make_checked_mapping(*values, **named_values)
        cls.__member_defaults = mapping

    @classmethod
    def defaults(cls):
        try:
            return cls.__member_defaults
        except AttributeError:
            cls.__member_defaults = {k: None for k in cls.names()}
            return cls.__member_defaults

    @classmethod
    def _make_checked_mapping(cls, *values, **named_values):
        """Generate key-value pairs where keys are strictly the names
        of the members of this Enum. Raises `KeyError` for both
        missing and invalid keys."""
        names = cls.names()
        defaults = cls.defaults()
        pairs = zip_longest(names, values, fillvalue=_FILL)
        mapping = dict(pairs, **named_values)
        if set(mapping) == set(names):
            return {k: (v if v is not _FILL else defaults[k])
                    for k, v in mapping.items()}
        else:
            invalid = set(mapping) - set(names)
            raise KeyError(f"{cls.__name__} requires keys {names}; "
                           f"invalid keys {invalid}")

    @classmethod
    def _make_casted_mapping(cls, *values, fillvalue=None, **named_values):
        """Like `_make_checked_mapping`, but values are casted based
        on the `types()` mapping"""
        # note that the `fillvalue` keyword-only arg is ignored
        mapping = cls._make_checked_mapping(*values, **named_values)
        types = cls.types()
        defaults = cls.defaults()
        return {k: (types[k](v) if v != defaults[k] and types[k] else v)
                for k, v in mapping.items()}
