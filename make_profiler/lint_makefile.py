import argparse
import re

from typing import Callable, Dict, List, Set, Tuple

from make_profiler.parser import parse
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


def parse_targets(ast: List[Tuple[str, Dict]]) -> Tuple[List[TargetData], Set[str]]:
    target_data = []
    deps_targets = set()

    for token_type, data in ast:
        if token_type != "target":
            continue

        target_data.append(TargetData(name=data["target"], doc=data["docs"]))

        for dep_arr in data["deps"]:
            for item in dep_arr:
                deps_targets.add(item)
                
    return target_data, deps_targets


def validate_target_comments(targets: List[TargetData], *args) -> bool:
    is_valid = True

    for t in targets:
        if not t.doc:
            print(f"Target without comments: {t.name}")
            is_valid = False

    return is_valid


def validate_orphan_targets(targets: List[TargetData], deps: Set[str]) -> bool:
    is_valid = True
    
    for t in targets:
        if t.name not in deps:
            if "[FINAL]" not in t.doc:
                print(f"{t.name}, is orphan - not marked as [FINAL] and no other target depends on it")
                is_valid = False

    return is_valid


def validate_spaces(lines: List[str]) -> bool:
    """Validate that no line starts with spaces.

    Lines that are a continuation of the previous one (the previous line
    ends with a backslash) are ignored as Makefiles often indent continued
    dependencies with spaces for readability.
    """

    is_valid = True

    for i, line in enumerate(lines):
        if not line:  # ignore empty lines
            continue
        # allow leading spaces if previous line ends with a backslash
        if i > 0 and lines[i - 1].rstrip().endswith("\\"):
            continue
        if line.startswith(" "):
            print(f"Line with extra spaces ({i}): {line}")
            is_valid = False

    return is_valid


TARGET_VALIDATORS: Callable[[List[TargetData], Set[str]], bool] = [validate_orphan_targets, validate_target_comments]
TEXT_VALIDATORS: Callable[[List[str]], bool] = [validate_spaces]


def validate(makefile_lines: List[str], targets: List[TargetData], deps: Set[str]):
    is_valid = True

    for validator in TEXT_VALIDATORS:
        is_valid = validator(makefile_lines) and is_valid

    for validator in TARGET_VALIDATORS:
        is_valid = validator(targets, deps) and is_valid

    return is_valid


def main():
    args = parse_args()
    
    with open(args.in_filename, "r") as f:
        makefile_lines = f.read().split("\n")

    # file_object is the stream of data and if once the data is consumed, you can't ask the source to give you the same data again.
    # so it's the reason why we should open in_file twice
    with open(args.in_filename, "r") as file:
        ast = parse(file)
    
    targets, deps = parse_targets(ast)

    if not validate(makefile_lines, targets, deps):
        raise ValueError(f"Houston, we have a problem.")


if __name__ == "__main__":
    main()
