import io
import pytest
from make_profiler import parser, lint_makefile


def test_missing_rule(capsys):
    mk = "all: foo\n"
    ast = parser.parse(io.StringIO(mk))
    targets, deps, dep_map = lint_makefile.parse_targets(ast)
    valid = lint_makefile.validate(mk.split('\n'), targets, deps, dep_map)
    captured = capsys.readouterr()
    assert not valid
    assert "No rule to make target 'foo', needed by 'all'" in captured.out


def test_spaces_after_multiline_continuation(capsys):
    mk = (
        "all: foo bar \\\n"
        "    baz ## [FINAL] deploy\n"
        "foo: ## first dep\n"
        "\t@echo foo\n"
        "bar: ## second dep\n"
        "\t@echo bar\n"
        "baz: ## third dep\n"
        "\t@echo baz\n"
    )
    ast = parser.parse(io.StringIO(mk))
    targets, deps, dep_map = lint_makefile.parse_targets(ast)
    valid = lint_makefile.validate(mk.split('\n'), targets, deps, dep_map)
    captured = capsys.readouterr()
    assert valid, captured.out


def test_trailing_spaces(capsys):
    mk = (
        "all: foo ## [FINAL] doc  \n"
        "\t@echo foo\n"
        "foo: ## doc\n"
        "\t@echo bar\n"
    )
    ast = parser.parse(io.StringIO(mk))
    targets, deps, dep_map = lint_makefile.parse_targets(ast)
    valid = lint_makefile.validate(mk.split('\n'), targets, deps, dep_map)
    captured = capsys.readouterr()
    assert not valid
    assert "Trailing spaces" in captured.out


def test_space_instead_of_tab(capsys):
    mk = (
        "all: ## [FINAL] doc\n"
        "  @echo foo\n"
    )
    ast = parser.parse(io.StringIO(mk))
    targets, deps, dep_map = lint_makefile.parse_targets(ast)
    valid = lint_makefile.validate(mk.split('\n'), targets, deps, dep_map)
    captured = capsys.readouterr()
    assert not valid
    assert "Space instead of tab" in captured.out


def test_main_reports_summary(tmp_path, monkeypatch, capsys):
    mk = "all: foo\n"
    mfile = tmp_path / "Makefile"
    mfile.write_text(mk)
    monkeypatch.setattr("sys.argv", ["profile_make_lint", "--in_filename", str(mfile)])
    ret = lint_makefile.main()
    captured = capsys.readouterr()
    assert ret == 1
    assert "validation failed" in captured.err.lower()
    assert "no rule to make target 'foo', needed by 'all'" in captured.err


