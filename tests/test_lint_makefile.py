import io
import pytest
from make_profiler import parser, lint_makefile


def run_validation(mk: str) -> tuple[bool, list[lint_makefile.LintError]]:
    ast = parser.parse(io.StringIO(mk))
    targets, deps, dep_map = lint_makefile.parse_targets(ast)
    errors: list[lint_makefile.LintError] = []
    valid = lint_makefile.validate(mk.split('\n'), targets, deps, dep_map, errors=errors)
    return valid, errors


def test_missing_rule():
    mk = "all: foo\n"
    valid, errors = run_validation(mk)
    assert not valid
    assert any(err.type == "missing rule" for err in errors)


def test_spaces_after_multiline_continuation():
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
    valid, errors = run_validation(mk)
    assert valid, errors


def test_trailing_spaces():
    mk = (
        "all: foo ## [FINAL] doc  \n"
        "\t@echo foo\n"
        "foo: ## doc\n"
        "\t@echo bar\n"
    )
    valid, errors = run_validation(mk)
    assert not valid
    assert any(err.type == "trailing spaces" for err in errors)


def test_space_instead_of_tab():
    mk = (
        "all: ## [FINAL] doc\n"
        "  @echo foo\n"
    )
    valid, errors = run_validation(mk)
    assert not valid
    assert any(err.type == "space instead of tab" for err in errors)


def test_error_includes_line_info():
    mk = (
        "all: foo ## [FINAL] doc  \n"
        "\t@echo foo\n"
    )
    valid, errors = run_validation(mk)
    assert not valid
    trailing = next(err for err in errors if err.type == "trailing spaces")
    expected_line = next(
        i for i, line in enumerate(mk.split("\n")) if line.endswith("  ")
    )
    assert trailing.line_number == expected_line
    assert trailing.line_text.endswith("  ")


def test_orphan_and_no_docs():
    mk = "foo:\n\t@echo foo\n"
    valid, errors = run_validation(mk)
    assert not valid
    types = {e.type for e in errors}
    assert "orphan target" in types
    assert "target without comments" in types


def test_main_reports_summary(tmp_path, monkeypatch, capsys):
    mk = "all: foo\n"
    mfile = tmp_path / "Makefile"
    mfile.write_text(mk)
    monkeypatch.setattr("sys.argv", ["profile_make_lint", "--in_filename", str(mfile)])
    ret = lint_makefile.main()
    captured = capsys.readouterr()
    assert ret == 1
    assert "validation failed" in captured.err.lower()
    assert "missing rule: 1" in captured.err


def test_summary_counts_similar_errors():
    errors = [
        lint_makefile.LintError(type="space instead of tab", message=""),
        lint_makefile.LintError(type="space instead of tab", message=""),
        lint_makefile.LintError(type="space instead of tab", message=""),
        lint_makefile.LintError(type="missing rule", message=""),
    ]
    summary = lint_makefile.summarize_errors(errors)
    assert "space instead of tab: 3" in summary
    assert "missing rule: 1" in summary


