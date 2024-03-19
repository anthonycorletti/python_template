import json
import sys
import urllib.request
from enum import Enum, unique
from typing import Dict, List, Optional

import toml
from invoke import Context, task
from packaging.requirements import Requirement, SpecifierSet

from python_template import __version__

PACKAGE_NAME = "python_template"
VERSION_FILE = f"{PACKAGE_NAME}/__init__.py"
PYPROJECT_TOML_FILENAME = "pyproject.toml"


def _check_pty() -> bool:
    return sys.platform not in ["win32", "cygwin", "msys"]


@unique
class BumpType(Enum):
    MAJOR = "major"
    MINOR = "minor"


@unique
class DepencencyAction(Enum):
    add = "add"
    remove = "remove"


def _bump_version_string(version: str, bump: Optional[BumpType] = None) -> str:
    """Bump a version string.

    Args:
        version (str): The version string to bump.
        bump (str): The type of bump to perform.

    Returns:
        str: The bumped version string.
    """
    from packaging.version import Version

    v = Version(version)
    if bump == BumpType.MAJOR:
        v = Version(f"{v.major + 1}.0.0")
    elif bump == BumpType.MINOR:
        v = Version(f"{v.major}.{v.minor + 1}.0")
    else:
        v = Version(f"{v.major}.{v.minor}.{v.micro + 1}")
    return str(v)


def _update_pyproject_toml(
    packages: List[str],
    dependency_action: DepencencyAction,
    dependency_group_name: Optional[str] = None,
) -> None:
    pyproject_toml = toml.load(PYPROJECT_TOML_FILENAME)

    current_deps = _get_reqs_from_pyproject_toml(
        pyproject_toml=pyproject_toml,
        dependency_group_name=dependency_group_name,
    )
    requested_deps = _get_requested_reqs(
        packages=packages,
    )

    result = dict()
    if dependency_action == DepencencyAction.add:
        # for all the add requests, check if the dependency is already installed
        # if the dependency is already installed, remove it from the current deps
        # add the requested dependency to the result
        # add the remaining current deps to the result
        # if there are no requested deps, then just re-install the current deps
        for name, requested_dep in requested_deps.items():
            if name in current_deps:
                current_deps.pop(name)
            result[name] = requested_dep
        result.update(current_deps)
    elif dependency_action == DepencencyAction.remove:
        # for all the remove requests, check if the dependency is already installed
        # if the dependency is installed, remove it from the current deps
        for name, current_dep in current_deps.items():
            if name not in requested_deps:
                result[name] = current_dep
    else:
        raise ValueError(
            f"Invalid dependency action: {dependency_action}. "
            f"Valid options are: {DepencencyAction.add}, "
            f"{DepencencyAction.remove}"
        )

    result_list = sorted([str(v) for v in result.values()])

    if dependency_group_name is not None:
        pyproject_toml["project"]["optional-dependencies"][dependency_group_name] = (
            result_list
        )
    else:
        pyproject_toml["project"]["dependencies"] = result_list

    with open(PYPROJECT_TOML_FILENAME, "w") as f:
        toml.dump(pyproject_toml, f, encoder=TomlEncoder())


class TomlEncoder(toml.TomlEncoder):
    def __init__(self, _dict: type = dict, preserve: bool = False) -> None:
        super().__init__(_dict=_dict, preserve=preserve)
        self.dump_funcs[str] = self._dump_str

    def _dump_str(self, v: str) -> str:
        if v.startswith("/("):
            result = "'''\n" + v + "'''"
        else:
            result = toml.encoder._dump_str(v)  # type: ignore
        if result.startswith('"^') or result.endswith('$"'):
            result = "'" + result + "'"
            result = result.replace('"', "")
        return result.replace("\\\\", "\\")


def _get_full_requirement_spec(package: str) -> Requirement:
    r = Requirement(package)
    if r.specifier is not None and r.specifier != "":
        r.specifier = _get_package_version_from_pypi(r)
    return r


def _get_package_version_from_pypi(r: Requirement) -> SpecifierSet:
    req = urllib.request.Request(f"https://pypi.org/pypi/{r.name}/json")
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode("utf-8"))
        return SpecifierSet(f'>={data["info"]["version"]}')


def _get_reqs_from_pyproject_toml(
    pyproject_toml: Dict,
    dependency_group_name: Optional[str] = None,
) -> Dict[str, Requirement]:
    project = pyproject_toml["project"]
    dep_list = project["dependencies"]
    if dependency_group_name:
        dep_list = project["optional-dependencies"][dependency_group_name]
    return {Requirement(d).name: Requirement(d) for d in dep_list}


def _get_requested_reqs(packages: List[str]) -> Dict[str, Requirement]:
    result = dict()
    for package in packages:
        r = _get_full_requirement_spec(package=package)
        result[r.name] = r
    return result


@task
def build(ctx: Context) -> None:
    """Build python_template."""
    ctx.run(
        "python -m build",
        pty=_check_pty(),
        echo=True,
    )


@task(aliases=["bv"])
def bump_version(ctx: Context, part: Optional[BumpType] = None) -> None:
    """Bump the version of python_template."""
    print(f"Current version: {__version__}")
    new_version = _bump_version_string(__version__, part)
    with open(VERSION_FILE, "r") as f:
        lines = f.readlines()
    with open(VERSION_FILE, "w") as f:
        for line in lines:
            if line.startswith("__version__"):
                f.write(f'__version__ = "{new_version}"\n')
            else:
                f.write(line)
    print(f"New version: {new_version}")


@task
def clean(ctx: Context) -> None:
    """Clean up the project."""
    ctx.run(
        " ".join(
            [
                "rm -rf",
                "build",
                "dist",
                "site",
                "htmlcov",
                ".mypy_cache",
                ".pytest_cache",
                ".ruff_cache",
                "*.egg-info",
                "coverage.xml",
                ".coverage",
            ]
        ),
        pty=_check_pty(),
        echo=True,
    )


@task
def format(ctx: Context) -> None:
    """Format the codebase."""
    ctx.run(
        "ruff format",
        pty=_check_pty(),
        echo=True,
    )


@task
def lint(ctx: Context) -> None:
    """Run the linters."""
    # NOTE: mypy requires the . to be present and will also respect the pyproject.toml
    ctx.run(
        "mypy .",
        pty=_check_pty(),
        echo=True,
    )
    ctx.run(
        "ruff check",
        pty=_check_pty(),
        echo=True,
    )


@task
def all(ctx: Context) -> None:
    """Run tasks for local development."""
    clean(ctx)
    install(ctx, groups=["dev"])
    format(ctx)
    lint(ctx)
    test(ctx)


@task
def publish(ctx: Context) -> None:
    """Publish python_template to PyPI."""
    ctx.run(
        "twine upload dist/*",
        pty=_check_pty(),
        echo=True,
    )


@task(iterable=["groups"])
def install(
    ctx: Context, editable: bool = True, groups: Optional[List[str]] = None
) -> None:
    """Install python_template."""
    if groups is None:
        _groups = ""
    else:
        _groups = f'[{",".join(groups)}]'

    if editable:
        _editable = "-e "
    else:
        _editable = ""
    ctx.run(
        f"pip install {_editable}.{_groups}",
        pty=_check_pty(),
        echo=True,
    )


@task(iterable=["packages"])
def add(
    ctx: Context,
    packages: List[str],
    reinstall: bool = True,
    group: Optional[str] = None,
) -> None:
    """Add dependencies to pyproject.toml.

    Args:
        ctx (Context): The invoke context.
        packages (List[str]): The packages to add.
        install (bool): Whether to install the packages after adding them.
            Defaults to True.
        group (Optional[str]): The group to add the packages to.
            Defaults to None.
    """
    msg = f"Adding {packages}"
    if group is not None:
        msg += f" to group {group}"
    print(msg)
    _update_pyproject_toml(
        packages=packages,
        dependency_action=DepencencyAction.add,
        dependency_group_name=group,
    )
    if reinstall:
        if group is not None:
            install(ctx, groups=[group])
        else:
            install(ctx, groups=["dev"])


@task(iterable=["packages"])
def remove(
    ctx: Context,
    packages: List[str],
    reinstall: bool = True,
    group: Optional[str] = None,
) -> None:
    """Remove dependencies from pyproject.toml.

    Args:
        ctx (Context): The invoke context.
        packages (List[str]): The packages to add.
        install (bool): Whether to install the packages after adding them.
            Defaults to True.
        group (Optional[str]): The group to add the packages to.
            Defaults to None.
    """
    _update_pyproject_toml(
        packages=packages,
        dependency_action=DepencencyAction.remove,
        dependency_group_name=group,
    )
    ctx.run(
        " ".join(
            [
                "pip",
                "uninstall",
                "-y",
                *packages,
            ]
        ),
        pty=_check_pty(),
        echo=True,
    )
    if reinstall:
        if group is not None:
            install(ctx, groups=[group])
        else:
            install(ctx, groups=["dev"])


@task
def test(ctx: Context) -> None:
    """Runs the pytest test suite."""
    ctx.run(
        "pytest",
        pty=_check_pty(),
        echo=True,
    )


@task
def version(ctx: Context) -> None:
    """Prints the version of python_template."""
    ctx.run(
        f"echo {__version__}",
        pty=_check_pty(),
        echo=True,
        nl=False,
    )
