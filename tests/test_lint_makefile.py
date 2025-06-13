import io
from make_profiler import parser, lint_makefile


def test_missing_rule(capsys):
    mk = "all: foo\n"
    ast = parser.parse(io.StringIO(mk))
    targets, deps, dep_map = lint_makefile.parse_targets(ast)
    valid = lint_makefile.validate(mk.split('\n'), targets, deps, dep_map)
    captured = capsys.readouterr()
    assert not valid
    assert "No rule to make target 'foo', needed by 'all'" in captured.out
