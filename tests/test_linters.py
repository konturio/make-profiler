import subprocess
import sys


def test_pylint_runs_clean() -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pylint",
            "--disable=all",
            "--enable=E",
            "make_profiler/lint_makefile.py",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=True,
    )


def test_ruff_runs_clean() -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "make_profiler/lint_makefile.py",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=True,
    )
