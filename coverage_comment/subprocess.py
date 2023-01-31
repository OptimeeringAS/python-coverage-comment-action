import functools
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
    cwd = ""

    def _git(self, *args, **kwargs):
        try:
            return run(
                "git",
                *args,
                cwd=self.cwd,
                **kwargs,
            )
        except SubProcessError as exc:
            raise GitError from exc

    def __getattr__(self, name: str) -> Any:
        return functools.partial(self._git, name)


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
