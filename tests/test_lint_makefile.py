import make_profiler.lint_makefile as lint


def test_allow_multiline_indentation():
    lines = [
        "target: \\",
        "    dep1 \\",
        "    dep2",
    ]
    assert lint.validate_spaces(lines)


def test_reject_leading_spaces():
    lines = [
        "target:",
        "  not_allowed",
    ]
    assert not lint.validate_spaces(lines)
