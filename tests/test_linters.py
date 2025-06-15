import subprocess


def test_pylint_runs_clean() -> None:
    result = subprocess.run(
        [
            "pylint",
            "--disable=all",
            "--enable=E",
            "make_profiler/lint_makefile.py",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert result.returncode == 0, result.stdout


def test_ruff_runs_clean() -> None:
    result = subprocess.run(
        ["ruff", "check", "make_profiler/lint_makefile.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert result.returncode == 0, result.stdout
