import io
from make_profiler.dot_export import export_dot
from make_profiler import parser

def build_sample():
    influences = {'b': {'a'}, 'a': set()}
    dependencies = {'a': [['b'], []], 'b': [[], []]}
    order_only = set()
    performance = {}
    indirect = {'a': set(), 'b': set()}
    docs = {'a': 'A doc', 'b': 'B doc'}
    return influences, dependencies, order_only, performance, indirect, docs

def test_export_contains_edge_and_clusters():
    inf, deps, order, perf, ind, docs = build_sample()
    f = io.StringIO()
    export_dot(f, inf, deps, order, perf, ind, docs)
    data = f.getvalue()
    assert 'b -> a' in data
    assert 'subgraph cluster_inputs' in data
    assert 'subgraph cluster_result' in data


def test_export_escapes_special_chars():
    inf = {'a"b': set()}
    deps = {'a"b': [[], []]}
    order = set()
    perf = {}
    ind = {'a"b': set()}
    docs = {'a"b': 'A "quote" doc'}
    f = io.StringIO()
    export_dot(f, inf, deps, order, perf, ind, docs)
    data = f.getvalue()
    assert '"a\\"b"' in data
    assert 'A \\"quote\\" doc' in data


def test_example_makefile_from_readme():
    with open('test/example.mk') as fh:
        ast = parser.parse(fh)
    deps, influences, order_only, indirect = parser.get_dependencies_influences(ast)
    docs = {i[1]['target']: i[1]['docs'] for i in ast if i[0] == parser.Tokens.target}
    f = io.StringIO()
    export_dot(f, influences, deps, order_only, {}, indirect, docs)
    data = f.getvalue()
    assert 'target1 -> all' in data
    assert 'subgraph cluster_inputs' in data
    assert 'label=Input' in data
