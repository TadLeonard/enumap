# Enumap: ordered data kept orderly


`Enumap` is an `Enum` that helps you manage named, ordered values in a strict but convenient way.
`Enumap` isn't yet another collection, 
it's a store of keys that creates familiar ordered collections in a
more expressive and less error prone way.

## Make a specification for your data
Make a spec for your data with a simple, declarative `Enum`:
```python
>>> from enumap import Enumap
>>> class Pie(Enumap):
...    rhubarb = "tart"
...    cherry = "sweet"
...    mud = "savory"
```

Or use the equivalent functional style:
```python
>>> Pie = Enumap("Pie", "rhubarb cherry mud")
```

## Easily create ordered collections from your data spec
`Enumap.map` and `Enumap.tuple` make familiar, reliable `OrderedDicts` and `namedtuples`
with the same fields and ordering you used in your data spec.
```python
>>> Pie.map(10, 23, mud=1)  # args and/or kwargs
OrderedDict([('rhubarb', 10), ('cherry', 23), ('mud', 1)])
>>> Pie.tuple(10, 23, 1000, cherry=1)  # override with kwargs
Pie_tuple(rhubarb=10, cherry=1, mud=1000)
```

## Discover errors when your collections are *created*, not when they're used
`KeyErrors` keep you from going astray:
```python
>>> Pie.tuple(rhubarb=1, cherry=1, mud=3, blueberry=30)
...
KeyError: "Pie requires keys ('rhubarb', 'cherry', 'mud'); got invalid keys {'blueberry'}"
>>> Pie.map(1, 1)
...
KeyError: "Pie requires keys ('rhubarb', 'cherry', 'mud'); missing keys {'mud'}"
```

With the `Enumap` data spec guiding you, you'll never let spelling errors seep deeper into your code:
```python
>>> data = {"rhubarb": 10, "cherry": 23, "mud": 1}
>>> # elsewhere in your code
... new_data = dict(data, chery=0)  # 'cherry' is mispelled, but your dictionary doesn't care
>>> # even deeper into your code
... if not new_data["cherry"]:
...     # this block won't execute thanks to our spelling error earlier on!
```

## Compose data safely with a single source for its order and naming
The `Enumap` spec acts like a tiny API for manipulating your data:
```python
>>> data = Pie.tuple(10, 23, 1)
>>> new_data = Pie(*data, rhubarb=data.rhubarb * 2)  # customer wants more rhubarb
>>> bad_data = Pie(*data, chery=0)  # you'll know right away that you've mispelled 'cherry'
KeyError: "Pie requires keys ('rhubarb', 'cherry', 'mud'); got invalid keys {'chery'}"
```

## Simple deserialization with type annotations
If you annotate your data fields with callable types, `Enumap.tuple_casted`
and `Enumap.map_casted` will create deserialized collections from your data:
```python
>>> import arrow  # convenient datetime library
>>> from enum import auto
>>> class CustomerOrder(Enumap):
...    index: int = "Order ID"
...    cost: Decimal = "Total pretax cost"
...    due_on: arrow.get = "Delivery date"
...
>>> serialized = "134,25014.99,2017-06-20"  # line from a CSV, for example
>>> CustomerOrder.tuple_casted(*serialized.split(","))
CustomerOrder_tuple(index=134, cost=Decimal('25014.99'), due_on=<Arrow [2017-06-20T00:00:00+00:00]>)
```

If you hate type annotations or if you prefer the functional
`Enum` constructor, use `Enumap.set_types`:
```python
>>> CustomerOrder.set_types(int, cost=Decimal, due_on=arrow.get)
>>> CustomerOrder.map_casted("22", "99.99", "2017-06-20")
OrderedDict([('index', 134), ('cost', Decimal('25014.99')), ...])
```

## Sparse collections with the less strict `SparseEnumap`
Create collections with `None` defaults:
```python
>>> from enumap import SparseEnumap
>>> SparsePie = SparseEnumap("SparsePie", "rhubarb cherry mud")
>>> SparsePie.tuple()
SparsePie_tuple(rhubarb=None, cherry=None, mud=None)
>>> SparsePie.tuple(2, cherry=1)
SparsePie_tuple(rhubarb=2, cherry=1, mud=None)
```

Still, invalid keys are not allowed:
```python
>>> SparsePie.tuple(cherry=1, rhubarb=1, mud=3, blueberry=30)
...
KeyError: "SparsePie has keys ('rhubarb', 'cherry', 'mud'); got invalid keys {'blueberry'}"
```

# Why?
`Enumap` lets you define a set of keys or field names in your *once* in your code. This means:

1. You get a single place to declaratively define an
   immutable set of keys or field names
2. You can refer back to your keys and field names elsewhere without the
   uncertainty of using string literals or hard-to-debug global variables
3. You can make containers from your keys without worrying that you've
   omitted or mispelled a key or field name

## Why not just dictionaries with string keys?
String literals make fine dictionary keys for small projects.

```python
data = dict(assembly="A1", reference="R3",
            name="resistor", subassembly=["U3", "W12"])
...

# later on
part_reference = data["reference"]
```

When a project grows beyond a certain size, you often see people keeping
field names bound to global variables so that they can be imported in other
modules. Usually the motivation for doing this is to improve clarity and
ease refactoring.

```python
PART_ASSEMBLY = "assembly"
PART_REFERENCE = "reference"
PART_SUBASSEMBLY = "subassembly"
PART_NAME = "name"
...
```

...and later they might use these global variables as dictionary keys:

```python
assembly = data[PART_ASSEMBLY]
subassembly = data.get(PART_SUBASSEMBLY, [])
...
```

After a while it might be tempting to group key variables in an empty class:

```python
class Part:
    assembly = "assembly"
    reference = "reference"
    ...

assembly = data[Part.assembly]
...
```

Now the code is more refactorable and less prone to error,
but later on we may want a modified copy of our dictionary:

```python
new_data = dict(data, asembly="A2")  # "assembly" is misspelled!
```

Now we've regressed to using plain strings and our code is prone to error
once more. We could get around this by using advanced dictionary unpacking:

```python
new_data = {**data, **{Part.assembly: "A2"}}
```

... but we've sacrificed readability for the sake of correctness.


## How about plain `namedtuple`s?
Namedtuples are great for making your code correct. They're ordered,
immutable, and they insist on the field names they were born with.
```python
Part = namedtuple("Part", "assembly reference subassembly name")
data = Part(assembly="A1", name="resistor", reference="R3", subassembly=[])
```

Looks great so far. We've got objects to pass around with immutable fields
and convenient, expressive attribute access. Let's say we want to JSONify
a `Part`. We'll want to convert it to a `dict`:
```python
data_as_dict = data._as_dict()
```

So now we're left using a private `namedtuple` method just to
get a dictionary out of our data! Say we're not done yet and we want
to update a field in our dictionary before sending it out as JSON:
```python
data_as_dict.update(asembly="A2")  # misspelled "assembly" error will go completely unnoticed!
```

Often we'll want to access our field names programmatically. Sadly, this also
requires accessing a private `namedtuple` attribute. Say we're writing
`namedtuple`s to a CSV file:
```python
csvwriter.write_header(Part._fields)
```

:toilet: Gross! Another private attribute!


## How about regular ol' `Enum` members as keys?
`Enum` makes your code more debuggable. When you use `Enum` members as keys
and parameters in your project, you never again have to wonder where literal
strings like 'asembly' came from in a `KeyError` traceback. They're created
in a clean, declarative fashion and they're immutable.

```python
Part = Enum("Part", "assembly reference subassembly name")
part = {Part.assembly: "A1", Part.name: "resistor", ...}
```

At this point we have a `part` dictionary whose keys are easily debuggable
`Enum` members. The problem is that you lose expressiveness when you create
collections out of their members:

```python
part.update({Part.assembly: "A2"})  # Enum members can't be **kwarg keys!
part[Part.assembly]  # lots of repetition and typing for something so simple
```

Our collection is no longer very REPL-friendly:
```python
>>> part
{<Part.assembly: 0>: 'A2', <Part.subassembly: 1>: []...}
```

Also, you may eventually want to get your collections' keys back into plain
string form (say, for JSONifying them):
```python
jsonifyable_part = {key.name: value for key, value in part.items()}
```

... and nobody has time for that.


## `Enumap`: expressive *and* strict
With `Enumap`, you get an immutable collection of keys from which you can
create `dict`s and `namedtuple`s. This approach gives you the best of both
worlds: expressive, familiar data structures constructed by the same
object that holds the keys, so incorrect keys will be discovered at the time
your collections are *made*, not when they're used later on.

```python
Part = Enumap("Part", "assembly reference subassembly name")
part_map = Part.map("A1", "R3", subassembly=[], name="resistor")
part = Part.tuple("A1", "R3", [], name="resistor")
```

If you use `Part` every time you want a new collection, you'll never let an
invalid key pass silently through your code:

```python
new_part_map = Part.map(*part_map.values(), assembly="A2")  # override assembly
new_part = Part.tuple(*part, assembly="A2")
```

# Installation
[![PyPI version](https://badge.fury.io/py/enumap.svg)](https://badge.fury.io/py/enumap)

Install with `pip install enumap`. Requires Python 3.6+.
