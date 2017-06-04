from timeit import timeit
from enumap import SparseEnumap, Enumap
from collections import namedtuple, OrderedDict


N_RUNS = 100_000


def test_smallish_sparse_tuple():
    data = "1 2 3 4 5 6 7 8 9 10 11".split()
    incomplete_data = data[:-1]
    sparse_spec = SparseEnumap("ThingSparse", "a b c d e f g h i j k")
    spec = Enumap("Thing", sparse_spec.names())

    print()
    print(spec.tuple(*data))
    print(spec.tuple(*data, d="override"))
    print(sparse_spec.tuple(*incomplete_data))

    # time Enumap.tuple() when all data is given
    enumap_tuple_time = timeit(
        "spec.tuple(*data)",
        globals=dict(data=data, spec=spec),
        number=N_RUNS)

    # time Enumap.tuple() when data is given with overrides
    enumap_override_tuple_time = timeit(
        "spec.tuple(*data, d='override')",
        globals=dict(data=data, spec=spec),
        number=N_RUNS)

    # time SparseEnumap.tuple() when partial data is given
    enumap_sparse_tuple_time = timeit(
        "spec.tuple(*data)",
        globals=dict(data=incomplete_data, spec=sparse_spec),
        number=N_RUNS)

    # time a regular tuple(iterable) call
    regular_tuple_time = timeit("tuple(data)",
                                globals=dict(data=data),
                                number=N_RUNS)

    # time a regular namedtuple(*args) call
    ntuple = namedtuple("ntuple", list(spec.names()))
    named_tuple_time = timeit("ntuple(*data)",
                              globals=dict(data=data, ntuple=ntuple),
                              number=N_RUNS)

    print(f"{'Enumap.tuple':<30} {enumap_tuple_time:.2f}")
    print(f"{'Enumap.tuple (with override)':<30} {enumap_override_tuple_time:.2f}")
    print(f"{'Enumap.tuple (sparse)':<30} {enumap_sparse_tuple_time:.2f}")
    print(f"{'tuple':<30} {regular_tuple_time:.2f}")
    print(f"{'namedtuple':<30} {named_tuple_time:.2f}")


def test_smallish_sparse_map():
    data = "1 2 3 4 5 6 7 8 9 10 11".split()
    incomplete_data = data[:-1]
    sparse_spec = SparseEnumap("ThingSparse", "a b c d e f g h i j k")
    spec = Enumap("Thing", sparse_spec.names())

    print()
    print(spec.map(*data))
    print(spec.map(*data, d="override"))
    print(sparse_spec.map(*incomplete_data))

    # time Enumap.map() when all data is given
    enumap_map_time = timeit(
        "spec.map(*data)",
        globals=dict(data=data, spec=spec),
        number=N_RUNS)

    # time Enumap.map() when data is given with overrides
    enumap_override_map_time = timeit(
        "spec.map(*data, d='override')",
        globals=dict(data=data, spec=spec),
        number=N_RUNS)

    # time SparseEnumap.map() when partial data is given
    enumap_sparse_map_time = timeit(
        "spec.map(*data)",
        globals=dict(data=incomplete_data, spec=sparse_spec),
        number=N_RUNS)

    # time a regular dict(zip(...)) call
    regular_dict_time = timeit(
        "dict(zip(spec.names(), data))",
         globals=dict(data=data, spec=spec),
         number=N_RUNS)

    # time a regular OrderedDict(zip(...)) call
    ordered_dict_time = timeit(
        "OrderedDict(zip(spec.names(), data))",
        globals=dict(data=data, OrderedDict=OrderedDict, spec=spec),
        number=N_RUNS)

    print(f"{'Enumap.map':<30} {enumap_map_time:.2f}")
    print(f"{'Enumap.map (with override)':<30} {enumap_override_map_time:.2f}")
    print(f"{'Enumap.map (sparse)':<30} {enumap_sparse_map_time:.2f}")
    print(f"{'dict':<30} {regular_dict_time:.2f}")
    print(f"{'OrderedDict':<30} {ordered_dict_time:.2f}")


if __name__ == "__main__":
    test_smallish_sparse_tuple()
    test_smallish_sparse_map()

