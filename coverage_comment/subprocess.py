import functools
import os
import subprocess
from typing import Any


class SubProcessError(Exception):
    pass


class GitError(SubProcessError):
    pass


def run(*args, **kwargs) -> str:
    try:
        return subprocess.run(
            args,
            text=True,
            check=True,
            capture_output=True,
            **kwargs,
        ).stdout
    except subprocess.CalledProcessError as exc:
        raise SubProcessError("/n".join([exc.stdout, exc.stderr])) from exc


class Git:
    """
    Wrapper around calling git subprocesses in a way that reads a tiny bit like
    Python code.
    Call a method on git to call the corresponding subcommand (use `_` for `-`).
    Add string parameters for the rest of the command line.
    Returns stdout or raise GitError
    >>> git = Git()
    >>> git.clone(url)
    >>> git.commit("-m", message)
    >>> git.rev_parse("--short", "HEAD")
    """

    cwd = "."

    def _git(self, *args: str, env: dict[str, str] | None = None, **kwargs) -> str:
        # When setting the `env` argument to run, instead of inheriting env
        # vars from the current process, the whole environment of the
        # subprocess is whatever we pass. In other words, we can either
        # conditionally pass an `env` parameter, but it's less readable,
        # or we can always pass an `env` parameter, but in this case, we
        # need to always merge `os.environ` to it (and ensure our variables
        # have precedence)
        try:
            return run(
                "git",
                *args,
                cwd=self.cwd,
                env=os.environ | (env or {}),
                **kwargs,
            )
        except SubProcessError as exc:
            raise GitError from exc

    def __getattr__(self, name: str) -> Any:
        return functools.partial(self._git, name.replace("_", "-"))


def fix_ownership_issues(git: Git):
    # As of 2023-01-30, GitHub changed _something_ to the ownership of the git repo
    # which confuses git like hell:
    #
    #     fatal: detected dubious ownership in repository at '/github/workspace'
    #     To add an exception for this directory, call:
    #         git config --global --add safe.directory /github/workspace
    #
    # Of course, this makes sense only when the action runs in GHA, but it's harmless
    # when testing the action locally, except that it will add random trash to the
    # user's git config.
    #
    # From git's doc:
    # > This config setting is only respected when specified in a system or global
    # > config, not when it is specified in a repository config or via the command line
    # > option
    git.config("--global", "--add", "safe.directory", "/github/workspace")
