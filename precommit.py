#!/usr/bin/env python3
"""Run precommit checks on the repository."""
import argparse
import os
import pathlib
import re
import subprocess
import sys


def main() -> int:
    """Execute the main routine."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--overwrite",
        help="Overwrites the unformatted source files with the "
        "well-formatted code in place. If not set, "
        "an exception is raised if any of the files do not conform "
        "to the style guide.",
        action='store_true')

    args = parser.parse_args()

    overwrite = bool(args.overwrite)

    repo_root = pathlib.Path(__file__).parent

    if overwrite:
        print('Removing trailing whitespace...')
        for pth in (sorted((repo_root / "mapry").glob("**/*.py")) + sorted(
            (repo_root / "tests").glob("**/*.py"))):
            pth.write_text(
                re.sub(r'[ \t]+$', '', pth.read_text(), flags=re.MULTILINE))

    print("YAPF'ing...")
    if overwrite:
        # yapf: disable
        subprocess.check_call([
            "yapf", "--in-place", "--style=style.yapf", "--recursive",
            "tests", "mapry", "setup.py", "precommit.py"],
            cwd=str(repo_root))
        # yapf: enable
    else:
        # yapf: disable
        subprocess.check_call([
            "yapf", "--diff", "--style=style.yapf", "--recursive",
            "tests", "mapry", "setup.py", "precommit.py"],
            cwd=str(repo_root))
        # yapf: enable

    print("Mypy'ing...")
    subprocess.check_call(["mypy", "--strict", "mapry", "tests"],
                          cwd=str(repo_root))

    print("Isort'ing...")
    # yapf: disable
    isort_files = map(
        str,
        sorted((repo_root / "mapry").glob("**/*.py")) +
        sorted((repo_root / "tests").glob("**/*.py")))
    # yapf: enable

    if overwrite:
        # yapf: disable
        cmd = [
            "isort", "--balanced", "--multi-line", "4", "--line-width", "80",
            "--dont-skip", "__init__.py", "--project", "mapry"
        ]
        # yapf: enable
        cmd.extend(isort_files)
        subprocess.check_call(cmd)
    else:
        # yapf: disable
        cmd = [
            "isort",
            "--check-only",
            "--diff",
            "--balanced",
            "--multi-line", "4",
            "--line-width", "80",
            "--dont-skip", "__init__.py",
            "--project", "mapry"
        ]
        # yapf: enable
        cmd.extend(isort_files)
        subprocess.check_call(cmd)

    print("Pydocstyle'ing...")
    subprocess.check_call(["pydocstyle", "mapry"], cwd=str(repo_root))

    print("Pylint'ing...")
    subprocess.check_call(["pylint", "--rcfile=pylint.rc", "tests", "mapry"],
                          cwd=str(repo_root))

    print("Testing...")
    env = os.environ.copy()
    env['ICONTRACT_SLOW'] = 'true'

    # yapf: disable
    subprocess.check_call(
        ["coverage", "run",
         "--source", "mapry",
         "-m", "unittest", "discover", "tests"],
        cwd=str(repo_root),
        env=env)
    # yapf: enable

    subprocess.check_call(["coverage", "report"])

    print("Doctesting...")
    subprocess.check_call(
        [sys.executable, "-m", "doctest",
         str(repo_root / "README.rst")])

    for pth in sorted((repo_root / "mapry").glob("**/*.py")):
        subprocess.check_call([sys.executable, "-m", "doctest", str(pth)])

    print("pyicontract-lint'ing...")
    for pth in sorted((repo_root / "mapry").glob("**/*.py")):
        subprocess.check_call(["pyicontract-lint", str(pth)])

    print("Checking with twine ...")
    subprocess.check_call([sys.executable, "setup.py", "sdist"],
                          cwd=str(repo_root))

    subprocess.check_call(["twine", "check", "dist/*"], cwd=str(repo_root))

    return 0


if __name__ == "__main__":
    sys.exit(main())
