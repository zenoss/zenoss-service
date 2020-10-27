#!/usr/bin/env python2.7

from __future__ import print_function

import argparse
import imp
import os
import pkg_resources
import sys
import toposort

from itertools import chain, groupby

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
    for version, group in groupby(scripts, lambda x: x.version):
        dependencies = {
            script.name: set(script.dependencies)
            for script in group
        }
        ordered = toposort.toposort_flatten(dependencies)
        ordered_scripts = [
            next(s for s in scripts if s.name == name)
            for name in ordered
        ]
        result.append((version, ordered_scripts))
    sorted_result = sorted(result, lambda x: x[0])
    return tuple(chain.from_iterable(e[1] for e in sorted_result))


def get_service_context():
    try:
        return sm.ServiceContext()
    except sm.ServiceMigrationError as ex:
        print(
            "Couldn't generate service context: {}".format(ex),
            file=sys.stderr,
        )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run service definition migrations",
    )
    parser.add_argument(
        "--from", required=True, metavar="VERSION", dest="after",
        help="Run migrations targeted for releases after this version",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    from_version = pkg_resources.parse_version(args.after)

    path = os.path.join(os.path.dirname(__file__), "migrations")
    all_scripts = get_scripts(path)
    relevant_scripts = [
        script
        for script in all_scripts
        if script.version > from_version
    ]
    for script in sort_scripts(relevant_scripts):
        ctx = get_service_context()
        if ctx is None:
            print("Skipping migration {}.".format(script))
            continue
        try:
            updated = script.migrate(ctx)
            if updated:
                ctx.commit()
                print("Migration {} applied.".format(script))
            else:
                print("No changes applied for migration {}.".format(script))
        except Exception as ex:
            print(
                "Migration {0} failed: {1}".format(script, ex),
                file=sys.stderr,
            )
