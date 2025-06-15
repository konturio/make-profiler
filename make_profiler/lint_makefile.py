import argparse
import re

import sys
from typing import Callable, Dict, List, Set, Tuple

from make_profiler.parser import parse
import collections
import os
from dataclasses import dataclass


@dataclass
class LintError:
    """A machine readable lint error with useful context."""

    type: str
    message: str
    line_number: int | None = None
    line_text: str | None = None


def parse_args():
    parser = argparse.ArgumentParser(description="Makefile linter")
    parser.add_argument(
        "--in_filename",
        type=str,
        default="Makefile",
        help="Makefile to read (default %(default)s)",
    )

    return parser.parse_args()


@dataclass
class TargetData:
    name: str
    doc: str


def parse_targets(ast: List[Tuple[str, Dict]]) -> Tuple[List[TargetData], Set[str], Dict[str, Set[str]]]:
    target_data = []
    deps_targets = set()
    deps_map = collections.defaultdict(set)

    for token_type, data in ast:
        if token_type != "target":
            continue

        name = data["target"]
        target_data.append(TargetData(name=name, doc=data["docs"]))

        for dep_arr in data["deps"]:
            for item in dep_arr:
                deps_targets.add(item)
                deps_map[item].add(name)

    return target_data, deps_targets, deps_map


def validate_target_comments(targets: List[TargetData], *args, errors: List[LintError] | None = None) -> bool:
    """Ensure that every target has documentation."""
    is_valid = True

    for t in targets:
        if not t.doc:
            msg = f"Target without comments: {t.name}"
            print(msg)
            if errors is not None:
                errors.append(LintError(type="target without comments", message=msg))
            is_valid = False

    return is_valid


def validate_orphan_targets(targets: List[TargetData], deps: Set[str], *args, errors: List[LintError] | None = None) -> bool:
    """Check that every target is used or explicitly marked as FINAL."""
    is_valid = True

    for t in targets:
        if t.name not in deps and "[FINAL]" not in t.doc:
            msg = f"{t.name}, is orphan - not marked as [FINAL] and no other target depends on it"
            print(msg)
            if errors is not None:
                errors.append(LintError(type="orphan target", message=msg))
            is_valid = False

    return is_valid


def validate_missing_rules(
    targets: List[TargetData],
    deps: Set[str],
    deps_map: Dict[str, Set[str]],
    *,
    errors: List[LintError] | None = None,
) -> bool:
    """Report dependencies that do not have a rule or a file backing them."""
    is_valid = True

    target_names = {t.name for t in targets}
    for dep in deps:
        if dep not in target_names and not os.path.exists(dep):
            for parent in sorted(deps_map.get(dep, [])):
                msg = f"No rule to make target '{dep}', needed by '{parent}'"
                print(msg)
                if errors is not None:
                    errors.append(LintError(type="missing rule", message=msg))
            is_valid = False

    return is_valid


def validate_spaces(lines: List[str], *, errors: List[LintError] | None = None) -> bool:
    """Validate that there are no unwanted spaces in Makefile lines.

    Spaces at the beginning of a line are normally disallowed.  However
    Make allows a backslash (``\``) at the end of a line to indicate that
    the statement continues on the next line.  In such cases the
    following line usually begins with spaces for readability.  These
    spaces should not be considered an error.
    """

    is_valid = True
    prev_line = ""

    for i, line in enumerate(lines):
        # Skip the check for leading spaces if the previous line ends with
        # a continuation character.  Trailing spaces are still reported.
        if prev_line.rstrip().endswith("\\"):
            prev_line = line
            if line.rstrip() != line:
                msg = f"Trailing spaces ({i}): {line}"
                print(msg)
                if errors is not None:
                    errors.append(
                        LintError(
                            type="trailing spaces",
                            message=msg,
                            line_number=i,
                            line_text=line,
                        )
                    )
                is_valid = False
            continue

        if line.rstrip() != line:
            msg = f"Trailing spaces ({i}): {line}"
            print(msg)
            if errors is not None:
                errors.append(
                    LintError(
                        type="trailing spaces",
                        message=msg,
                        line_number=i,
                        line_text=line,
                    )
                )
            is_valid = False

        if line.startswith(" ") and not line.startswith("\t"):
            msg = f"Space instead of tab ({i}): {line}"
            print(msg)
            if errors is not None:
                errors.append(
                    LintError(
                        type="space instead of tab",
                        message=msg,
                        line_number=i,
                        line_text=line,
                    )
                )
            is_valid = False

        prev_line = line

    return is_valid


TARGET_VALIDATORS: Callable[[List[TargetData], Set[str], Dict[str, Set[str]]], bool] = [
    validate_orphan_targets,
    validate_target_comments,
    validate_missing_rules,
]
TEXT_VALIDATORS: Callable[[List[str]], bool] = [validate_spaces]


def validate(
    makefile_lines: List[str],
    targets: List[TargetData],
    deps: Set[str],
    deps_map: Dict[str, Set[str]],
    *,
    errors: List[LintError] | None = None,
) -> bool:
    """Run all validators and collect error messages."""
    is_valid = True

    for validator in TEXT_VALIDATORS:
        is_valid = validator(makefile_lines, errors=errors) and is_valid

    for validator in TARGET_VALIDATORS:
        is_valid = validator(targets, deps, deps_map, errors=errors) and is_valid

    return is_valid


def summarize_errors(errors: List[LintError]) -> str:
    """Return a short summary of lint errors."""

    counts = collections.Counter(err.type for err in errors)
    parts = [f"{name}: {count}" for name, count in sorted(counts.items())]
    return ", ".join(parts)


def main():
    args = parse_args()
    
    with open(args.in_filename, "r") as f:
        makefile_lines = f.read().split("\n")

    # file_object is the stream of data and if once the data is consumed, you can't ask the source to give you the same data again.
    # so it's the reason why we should open in_file twice
    with open(args.in_filename, "r") as file:
        ast = parse(file)

    targets, deps, deps_map = parse_targets(ast)

    errors: List[LintError] = []
    if not validate(makefile_lines, targets, deps, deps_map, errors=errors):
        summary = summarize_errors(errors)
        print(f"Makefile validation failed: {summary}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
