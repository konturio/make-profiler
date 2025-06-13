import argparse
import re

from typing import Callable, Dict, List, Set, Tuple

from make_profiler.parser import parse
import collections
import os
from dataclasses import dataclass


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


def validate_target_comments(targets: List[TargetData], *args) -> bool:
    is_valid = True

    for t in targets:
        if not t.doc:
            print(f"Target without comments: {t.name}")
            is_valid = False

    return is_valid


def validate_orphan_targets(targets: List[TargetData], deps: Set[str], *args) -> bool:
    is_valid = True
    
    for t in targets:
        if t.name not in deps:
            if "[FINAL]" not in t.doc:
                print(f"{t.name}, is orphan - not marked as [FINAL] and no other target depends on it")
                is_valid = False

    return is_valid


def validate_missing_rules(targets: List[TargetData], deps: Set[str], deps_map: Dict[str, Set[str]]) -> bool:
    is_valid = True

    target_names = {t.name for t in targets}
    for dep in deps:
        if dep not in target_names and not os.path.exists(dep):
            for parent in sorted(deps_map.get(dep, [])):
                print(f"No rule to make target '{dep}', needed by '{parent}'")
            is_valid = False

    return is_valid


def validate_spaces(lines: List[str]) -> bool:
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
                print(f"Line with extra spaces ({i}): {line}")
                is_valid = False
            continue

        if line.rstrip() != line or (line.startswith(" ") and not line.startswith("\t")):
            print(f"Line with extra spaces ({i}): {line}")
            is_valid = False

        prev_line = line

    return is_valid


TARGET_VALIDATORS: Callable[[List[TargetData], Set[str], Dict[str, Set[str]]], bool] = [
    validate_orphan_targets,
    validate_target_comments,
    validate_missing_rules,
]
TEXT_VALIDATORS: Callable[[List[str]], bool] = [validate_spaces]


def validate(makefile_lines: List[str], targets: List[TargetData], deps: Set[str], deps_map: Dict[str, Set[str]]):
    is_valid = True

    for validator in TEXT_VALIDATORS:
        is_valid = validator(makefile_lines) and is_valid

    for validator in TARGET_VALIDATORS:
        is_valid = validator(targets, deps, deps_map) and is_valid

    return is_valid


def main():
    args = parse_args()
    
    with open(args.in_filename, "r") as f:
        makefile_lines = f.read().split("\n")

    # file_object is the stream of data and if once the data is consumed, you can't ask the source to give you the same data again.
    # so it's the reason why we should open in_file twice
    with open(args.in_filename, "r") as file:
        ast = parse(file)

    targets, deps, deps_map = parse_targets(ast)

    if not validate(makefile_lines, targets, deps, deps_map):
        raise ValueError(f"Houston, we have a problem.")


if __name__ == "__main__":
    main()
