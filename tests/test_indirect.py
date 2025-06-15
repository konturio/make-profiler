import io
from make_profiler import parser


def test_indirect_influences_transitive():
    sample = (
        "target1: target2\n"
        "\ttrue\n"
        "target2: target3\n"
        "\ttrue\n"
        "target3:\n"
        "\ttrue\n"
    )
    ast = parser.parse(io.StringIO(sample))
    _, _, _, indirect = parser.get_dependencies_influences(ast)
    assert indirect['target3'] == {'target1'}
    assert indirect['target2'] == set()
    assert indirect['target1'] == set()


