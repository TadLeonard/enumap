"""Unit tests. Run with `py.test test.py -v`."""

import pytest
from collections import OrderedDict
from enumap import Enumap as EM, SparseEnumap as SEM
from decimal import Decimal


def test_map():
    a = EM("a", names="b c e")
    assert a.map(1, 2, 3, e=33) == \
           OrderedDict([('b', 1), ('c', 2), ('e', 33)])


def test_tuple():
    a = EM("a", names="b c e")
    assert a.tuple(1, 2, 3, e=33) == (1, 2, 33)


def test_ordering():
    a = EM("forward", names=["n" + str(i) for i in range(100)])
    b = EM("backward", names=["n" + str(i) for i in range(99, -1, -1)])
    expected_a = list(range(100))
    expected_a[42] = 9000
    assert list(a.tuple(*range(100), n42=9000)) == expected_a
    expected_b = list(range(100))
    expected_b[57] = 9000
    assert list(b.tuple(*range(100), n42=9000)) == expected_b


to_int = lambda num: int(float(num))


def test_map_casted_0():
    a = EM("a", names="b c e")
    a.set_types(to_int, to_int, float)
    assert a.map_casted(*"1 2.2 3.3".split()) == dict(b=1, c=2, e=3.3)


def test_map_casted_1():
    a = EM("a", names="b c e")
    a.set_types(to_int, to_int, float, e=to_int)
    assert a.map_casted(*"1 2.2 3.3".split()) == dict(b=1, c=2, e=3)


def test_tuple_casted_0():
    a = EM("a", names="b c e")
    a.set_types(to_int, to_int, float)
    assert a.tuple_casted(*"1 2.2 3.3".split()) == (1, 2, 3.3)


def test_tuple_casted_1():
    a = EM("a", names="b c e")
    a.set_types(to_int, to_int, float, e=to_int)
    assert a.tuple_casted(*"1 2.2 3.3".split(), b=2.2) == (2, 2, 3.0)


def test_annotated_tuple_casted():
    class Order(str, EM):
        index: int = "Order ID"
        cost: Decimal = "Total pretax cost"
        due_on: str = "Delivery date"

    assert Order.tuple_casted(*"12 142.22 2017-04-02".split()) == \
           (12, Decimal("142.22"), "2017-04-02")


def test_annotated_map_casted():
    class Order(str, EM):
        index: int = "Order ID"
        cost: Decimal = "Total pretax cost"
        due_on: str = "Delivery date"

    assert Order.map_casted(*"12 142.22 2017-04-07".split()) == \
           dict(index=12, cost=Decimal("142.22"), due_on="2017-04-07")


def test_names():
    assert list(EM("a", names="b c e").names()) == ["b", "c", "e"]


def test_tuple_class():
    a = EM("a", names="b c e")
    assert a.tuple_class()._fields == ("b", "c", "e")


def test_member_types():
    Pastry = EM("Pastry", names="croissant donut muffin")
    Pastry.set_types(int, int, int, donut=float)  # override donut with kwarg
    assert (Pastry.types() ==
            {'croissant': int, 'donut': float, 'muffin': int})


def test_missing_key():
    a = EM("a", names="b c e")
    with pytest.raises(KeyError) as ke:
        assert a.tuple(*"1 3".split())
    assert "missing keys {'e'}" in str(ke)


def test_bad_key():
    a = EM("a", names="b c e")
    with pytest.raises(KeyError) as ke:
        assert a.tuple(*"1 3 4".split(), f="nope")
    assert "invalid keys {'f'}" in str(ke)


def test_sparse_defaults():
    a = SEM("a", names="b c d e")
    a.set_defaults(c="WONK", d=0)
    assert a.tuple(**a.defaults()) == (None, "WONK", 0, None)


def test_sparse_tuple():
    a = SEM("a", names="b c d e")
    a.set_defaults(c="WONK", d=0)
    assert (a.tuple(*"1 3".split(), c="2.2") ==
            ("1", "2.2", 0, None))


def test_sparse_map():
    a = SEM("a", names="b c e")
    assert (a.map(*"1 3".split(), c="2.2") ==
            OrderedDict([("b", "1"), ("c", "2.2"), ("e", None)]))


def test_sparse_casted_tuple():
    a = SEM("a", names="a b c e")
    a.set_types(to_int, to_int, float, float)
    casted_tuple = a.tuple_casted(*"1.1 2.2 3.3".split())
    assert casted_tuple == (1, 2, 3.3, None)  # missing values aren't casted


def test_sparse_casted_tuple_with_default():
    a = SEM("a", names="a b c e")
    a.set_types(to_int, to_int, float, int)
    a.set_defaults(e="HOOP")
    casted_tuple = a.tuple_casted(*"1.1 2.2".split())
    assert casted_tuple == (1, 2, None, "HOOP")  # missing values aren't casted


def test_sparse_casted_map():
    a = SEM("a", names="a b c e")
    a.set_types(to_int, to_int, float, float)
    casted_map = a.map_casted(*"1.1 2.2 3.3".split())
    assert tuple(casted_map.values()) == (1, 2, 3.3, None)


def test_sparse_types():
    """Check that SparseEnumap's types can be sparse.
    Missing type callables won't be called on values."""
    a = SEM("a", names="a b c e")
    a.set_types(int, int, int)  # sparse types; only two of four set
    a.set_defaults(b=3000, c="heyo")
    assert a.tuple_casted("1", "1") == (1, 1, "heyo", None)


def test_sparse_annotations():
    """Check that SparseEnumap allows for sparse type annotations"""
    class A(SEM):
        a: float = 1
        b: float = 2
        c = 3
        d = 4

    assert dict(A.types()) == dict(a=float, b=float)
    assert dict(A.map_casted(*("1.2 1 hello world".split()))) == \
           dict(a=1.2, b=1.0, c="hello", d="world")


def test_too_many_args():
    """Ensure that Enumaps will not accept too many arguments"""
    class A(EM):
        a = 1
        b = 2
        c = 3

    with pytest.raises(KeyError) as e:
        A.tuple(3, 4, 5, 6)
    assert "expected 3 arguments, got 4" in str(e)

    with pytest.raises(KeyError) as e:
        A.map(3, 4, 5, 6)
    assert "expected 3 arguments, got 4" in str(e)


def test_too_many_args_casted():
    """Ensure that Enumaps will not accept too many arguments for
    *_casted methods"""
    class A(EM):
        a: int = 1
        b: int = 2
        c: int = 3

    with pytest.raises(KeyError) as e:
        A.tuple_casted(3, 4, 5, 6)
    assert "expected 3 arguments, got 4" in str(e)

    with pytest.raises(KeyError) as e:
        A.map_casted(3, 4, 5, 6)
    assert "expected 3 arguments, got 4" in str(e)


def test_too_many_args_sparse():
    """Ensure that SparseEnumaps will not accept too many arguments"""
    class A(SEM):
        a: int = 1
        b = 2
        c: int = 3

    with pytest.raises(KeyError) as e:
        A.tuple(3, 4, 5, 6)
    assert "expected 3 arguments, got 4" in str(e)

    with pytest.raises(KeyError) as e:
        A.map(3, 4, 5, 6)
    assert "expected 3 arguments, got 4" in str(e)


def test_typless():
    """Make sure types are allowed to be blank"""
    a = EM("A", "a b c".split())
    b = SEM("B", "a b c".split())
    assert a.types() == {}
    assert b.types() == {}


def test_too_many_args_sparse_casted():
    """Ensure that SparseEnumaps will not accept too many arguments for
    *_casted methods"""
    class A(SEM):
        a: int = 1
        b = 2
        c: int = 3

    with pytest.raises(KeyError) as e:
        A.tuple_casted(3, 4, 5, 6)
    assert "expected 3 arguments, got 4" in str(e)

    with pytest.raises(KeyError) as e:
        A.map_casted(3, 4, 5, 6)
    assert "expected 3 arguments, got 4" in str(e)


def test_nonsparse_types():
    a = EM("a", "a b c")
    a.set_types(a=int, b=int)
    assert a.types() == dict(a=int, b=int)


def test_sparse_bad_key():
    a = SEM("a", names="b c e")
    with pytest.raises(KeyError) as ke:
        assert a.tuple(*"1 3".split(), f="nope")
    assert "invalid keys {'f'}" in str(ke)


def test_copy_from_names():
    """Check that Enumap.names() can be used to construct another Enumap"""
    a = EM("a", "b c d")
    b = EM("b", a.names())
    assert a.map(*range(3)) == b.map(*range(3))
