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


def test_critical_path_handles_final_targets():
    """Ensure graph export works when a root target has no dependents."""
    inf = {'a': set()}
    deps = {'a': [[], []]}
    f = io.StringIO()
    export_dot(f, inf, deps, set(), {}, {'a': set()}, {'a': 'Doc'})
    data = f.getvalue()
    assert 'subgraph cluster_tools' in data


def test_example_makefile_from_readme():
    with open('test/example.mk', encoding='utf-8') as fh:
        ast = parser.parse(fh)
    deps, influences, order_only, indirect = parser.get_dependencies_influences(ast)
    docs = {i[1]['target']: i[1]['docs'] for i in ast if i[0] == parser.Tokens.target}
    f = io.StringIO()
    export_dot(f, influences, deps, order_only, {}, indirect, docs)
    data = f.getvalue()
    assert 'target1 -> all' in data
    assert 'subgraph cluster_inputs' in data
    assert 'label=Input' in data


def test_current_targets_are_highlighted():
    inf, deps, order, _, ind, docs = build_sample()
    perf = {
        'a': {'done': True, 'failed': False, 'isdir': False, 'current': True},
        'b': {'done': True, 'failed': False, 'isdir': False, 'current': False},
    }
    f = io.StringIO()
    export_dot(f, inf, deps, order, perf, ind, docs)
    data = f.getvalue()
    assert 'fillcolor="#0969DA"' in data
    assert 'fontcolor="#fff"' in data


def test_current_run_critical_path_colored():
    inf, deps, order, _, ind, docs = build_sample()
    perf = {
        'a': {'done': True, 'failed': False, 'isdir': False, 'current': True, 'timing_sec': 2},
        'b': {'done': True, 'failed': False, 'isdir': False, 'current': True, 'timing_sec': 1},
    }
    f = io.StringIO()
    export_dot(f, inf, deps, order, perf, ind, docs)
    data = f.getvalue()
    assert 'color="#800080"' in data
