#!/usr/bin/env python2.7

from __future__ import print_function

import argparse
import imp
import os
import pkg_resources
import sys
import toposort

from itertools import groupby

import Globals  # noqa: F401 because Zenoss

# Import _after_ importing Globals due to Zenoss Product dependencies
import servicemigration as sm
sm.require("1.1.16")


class Script(object):

    version = None
    script = None
    dependencies = None

    def __init__(self, script):
        self.version = pkg_resources.parse_version(script.version)
        self.dependencies = getattr(script, "dependencies", ())
        self.name = script.__name__
        if script.__doc__:
            desc = script.__doc__.replace("\n", " ").strip()
        else:
            desc = ""
        self.description = desc
        self.script = script
        self.__key = (self.version, self.script.__name__)

    def migrate(self, ctx, *args, **kw):
        return self.script.migrate(ctx, *args, **kw)

    def __lt__(self, other):
        return self.__key < other.__key

    def __le__(self, other):
        return self.__key <= other.__key

    def __gt__(self, other):
        return self.__key > other.__key

    def __ge__(self, other):
        return self.__key >= other.__key

    def __eq__(self, other):
        return self.__key == other.__key

    def __ne__(self, other):
        return self.__key != other.__key

    def __str__(self):
        return os.path.basename(self.script.__name__)


def list_script_files(path):
    for filename in os.listdir(path):
        if filename == "__init__.py" or filename[-3:] != ".py":
            continue
        yield filename


def get_scripts(path):
    scripts = []
    for filename in list_script_files(path):
        filepath = os.path.join(path, filename)
        script_name = filename[:-3]
        script = imp.load_source(script_name, filepath)
        if not (hasattr(script, "version") and hasattr(script, "migrate")):
            continue
        scripts.append(Script(script))
    return scripts


def sort_scripts(scripts):
    """Sort scripts into dependency order"""
    result = []

    def key_func(s):
        return s.version

    sorted_scripts = sorted(scripts, key=key_func)
    for version, group in groupby(sorted_scripts, key_func):
        dependencies = {
            script.name: set(script.dependencies)
            for script in group
        }
        ordered = toposort.toposort_flatten(dependencies)
        ordered_scripts = (
            next(s for s in scripts if s.name == name)
            for name in ordered
        )
        result.extend(ordered_scripts)
    return result


def get_service_context():
    try:
        return sm.ServiceContext()
    except sm.ServiceMigrationError as ex:
        print(
            "Couldn't generate service context: {}".format(ex),
            file=sys.stderr,
        )


class ListCommand(object):

    @classmethod
    def from_args(cls, args):
        cls(args)()

    def __init__(self, args):
        self.args = args

    def __call__(self):
        path = _get_migrations_dir()
        scripts = sort_scripts(get_scripts(path))

        if self.args.after:
            from_version = pkg_resources.parse_version(self.args.after)
            scripts = [s for s in scripts if s.version > from_version]

        if not scripts:
            return

        max_name_length = max(len(s.name) for s in scripts)
        for script in scripts:
            print(
                "{:{width}}  {:>6}  {}".format(
                    script.name, script.version, script.description,
                    width=max_name_length,
                )
            )


class RunCommand(object):

    @classmethod
    def from_args(cls, args):
        cls(args)()

    def __init__(self, args):
        self.args = args

    def __call__(self):
        path = _get_migrations_dir()
        self.all_scripts = get_scripts(path)

        from_version = self.args.after
        script_name = self.args.script

        if from_version:
            self._from(from_version)
        elif script_name:
            self._script(script_name)

    def _from(self, from_version):
        from_version = pkg_resources.parse_version(from_version)
        relevant_scripts = [
            script
            for script in self.all_scripts
            if script.version > from_version
        ]
        for script in sort_scripts(relevant_scripts):
            self._run(script)

    def _script(self, script_name):
        script = next(
            (s for s in self.all_scripts if s.name == script_name), None
        )
        if not script:
            print("script not found.")
            sys.exit(1)

        self._run(script)

    def _run(self, script):
        ctx = get_service_context()
        if ctx is None:
            print("Skipping migration {}.".format(script))
            return
        try:
            updated = script.migrate(ctx)
            if updated:
                if self.args.nocommit:
                    print("Unapplied changes for migration {}.".format(script))
                else:
                    ctx.commit()
                    print("Migration {} applied.".format(script))
            else:
                print("No changes applied for migration {}.".format(script))
        except Exception as ex:
            print(
                "Migration {0} failed: {1}".format(script, ex),
                file=sys.stderr,
            )


class DefaultSubcommandArgParse(argparse.ArgumentParser):
    __default_subparser = None

    def set_default_subparser(self, name):
        self.__default_subparser = name

    def _parse_known_args(self, arg_strings, *args, **kw):
        in_args = set(arg_strings)
        d_sp = self.__default_subparser
        if d_sp is not None and not {"-h", "--help"}.intersection(in_args):
            for x in self._subparsers._actions:
                subparser_found = (
                    isinstance(x, argparse._SubParsersAction) and
                    in_args.intersection(x._name_parser_map.keys())
                )
                if subparser_found:
                    break
            else:
                # insert default into first position.
                arg_strings = [d_sp] + arg_strings
        return super(DefaultSubcommandArgParse, self)._parse_known_args(
            arg_strings, *args, **kw
        )


def parse_args():
    parser = DefaultSubcommandArgParse(
        description="Run service definition migrations",
    )
    parser.set_default_subparser("run")

    subparsers = parser.add_subparsers(
        title="Commands",
    )

    run_parser = subparsers.add_parser(
        "run", help="Run migrations.  This is the default command."
    )
    run_parser.add_argument(
        "-t", "--no-commit", dest="nocommit", action="store_true",
        help="Do not commit changes to serviced.",
    )
    run_group = run_parser.add_mutually_exclusive_group(required=True)
    run_group.add_argument(
        "--from", metavar="VERSION", dest="after",
        help="Run migrations targeted for releases after this version",
    )
    run_group.add_argument(
        "--script", metavar="NAME", dest="script",
        help="Run this migration and all its dependencies.",
    )
    run_parser.set_defaults(func=RunCommand.from_args)

    list_parser = subparsers.add_parser(
        "list",
        description="Lists migration scripts in execution order.",
        help="List migrations.",
    )
    list_parser.add_argument(
        "--from", metavar="VERSION", dest="after",
        help="List migrations targeted for releases after this version",
    )
    list_parser.set_defaults(func=ListCommand.from_args)

    return parser.parse_args()


def _get_migrations_dir():
    return os.path.join(os.path.dirname(__file__), "migrations")


def main():
    args = parse_args()
    args.func(args)
