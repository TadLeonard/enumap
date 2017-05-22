"""Unit tests. Run with `py.test test.py -v`."""

from collections import OrderedDict
from enumap import MappableEnum as ME
from decimal import Decimal


def test_map():
    a = ME("a", names="b c e")
    assert a.map(1, 2, 3, e=33) == \
           OrderedDict([('b', 1), ('c', 2), ('e', 33)])


def test_tuple():
    a = ME("a", names="b c e")
    assert a.tuple(1, 2, 3, e=33) == (1, 2, 33)


def test_ordering():
    a = ME("forward", names=["n" + str(i) for i in range(100)])
    b = ME("backward", names=["n" + str(i) for i in range(99, -1, -1)])
    expected_a = list(range(100))
    expected_a[42] = 9000
    assert list(a.tuple(*range(100), n42=9000)) == expected_a
    expected_b = list(range(100))
    expected_b[57] = 9000
    assert list(b.tuple(*range(100), n42=9000)) == expected_b


to_int = lambda num: int(float(num))


def test_map_casted_0():
    a = ME("a", names="b c e")
    a.set_types(to_int, to_int, float)
    assert a.map_casted(*"1 2.2 3.3".split()) == dict(b=1, c=2, e=3.3)


def test_map_casted_1():
    a = ME("a", names="b c e")
    a.set_types(to_int, to_int, float, e=to_int)
    assert a.map_casted(*"1 2.2 3.3".split()) == dict(b=1, c=2, e=3)


def test_tuple_casted_0():
    a = ME("a", names="b c e")
    a.set_types(to_int, to_int, float)
    assert a.tuple_casted(*"1 2.2 3.3".split()) == (1, 2, 3.3)


def test_tuple_casted_1():
    a = ME("a", names="b c e")
    a.set_types(to_int, to_int, float, e=to_int)
    assert a.tuple_casted(*"1 2.2 3.3".split(), b=2.2) == (2, 2, 3.0)


def test_annotated_tuple_casted():
    class Order(str, ME):
       index: int = "Order ID"
       cost: Decimal = "Total pretax cost"
       due_on: str = "Delivery date"

    assert Order.tuple_casted(*"12 142.22 2017-04-02".split()) == \
           (12, Decimal("142.22"), "2017-04-02")


def test_annotated_map_casted():
    class Order(str, ME):
       index: int = "Order ID"
       cost: Decimal = "Total pretax cost"
       due_on: str = "Delivery date"

    assert Order.map_casted(*"12 142.22 2017-04-07".split()) == \
           dict(index=12, cost=Decimal("142.22"), due_on="2017-04-07")


def test_names():
    assert list(ME("a", names="b c e").names()) == ["b", "c", "e"]


def test_tuple_class():
    a = ME("a", names="b c e")
    assert a.tuple_class()._fields == ("b", "c", "e")


def test_member_types():
    Pastry = ME("Pastry", names="croissant donut muffin")
    Pastry.set_types(int, int, int, donut=float)  # override donut with kwarg
    assert (Pastry.types() ==
            {'croissant': int, 'donut': float, 'muffin': int})
