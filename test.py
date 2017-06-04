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


def test_sparse_mapping():
    a = SEM("a", names="b c e")
    assert a.tuple(*"1 3".split(), c="2.2") == ("1", "2.2", None)


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
