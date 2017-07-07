from collections import namedtuple, OrderedDict
from enum import Enum
from itertools import zip_longest


__version__ = "1.2.2"


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


_FILL = object()  # sentinal for missing values in sparse collections


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
            default_maker = Enumap(f"{cls.__name__}_defaults", cls.names())
            cls.__member_defaults = default_maker.map(*[None] * len(cls))
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
            cls._raise_invalid_args(values, mapping, names)

    @classmethod
    def _make_casted_mapping(cls, *values, fillvalue=None, **named_values):
        """Like `_make_checked_mapping`, but values are casted based
        on the `types()` mapping"""
        # note that the `fillvalue` keyword-only arg is ignored
        names = cls.names()
        mapping = dict(zip(names, values), **named_values)
        name_set = set(names)
        present = set(mapping)
        missing = name_set - present
        invalid = present - name_set
        if not invalid and len(values) <= len(names):
            types = cls.types()
            if types:
                mapping.update(((k, v(mapping[k]))
                                for k, v in types.items()
                                if k not in missing))
            defaults = cls.defaults()
            mapping.update(((k, defaults[k]) for k in missing))
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
