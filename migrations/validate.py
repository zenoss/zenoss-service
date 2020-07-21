#!/usr/bin/env python3

import argparse
import bisect
import subprocess
import sys

from git import Repo
from packaging.version import Version, parse as parse_version
from pathlib import Path

parser = argparse.ArgumentParser(description="Validate migrations")
parser.add_argument("target-version", type=str)
args = parser.parse_args()
target_version = getattr(args, "target-version")


cwd = Path.cwd()
paths = [cwd]
paths.extend(cwd.parents)

git_root = next((p for p in paths if (p / ".git").exists()), None)
if git_root is None:
    print("No git repo found in directory tree")
    sys.exit(1)

print(git_root)
repo = Repo(git_root)
print(dir(repo))

versions = sorted(
    (version, tag)
    for tag in repo.tags
    if isinstance(version := parse_version(tag.name), Version)
)
prior, prior_tag = versions[-1]
print(prior)

target = Version(target_version)
print(target)

test_output = (cwd / "test_output")
service_dump_path = (test_output / "Zenoss.cse")
service_dump_path.mkdir(parents=True, exist_ok=True)


# def list_paths(root_tree, path=Path(".")):
#     for blob in root_tree.blobs:
#         print(dir(blob))
#         # print(blob.stream_data(sys.stdout))
#         yield path / blob.name
#     for tree in root_tree.trees:
#         yield from list_paths(tree, path / tree.name)


# print(repo.tree(prior_tag))
root = repo.tree(prior_tag)
cse_tree = next(
    (t for t in root.traverse() if t.path == "services/Zenoss.cse"),
    None,
)
if cse_tree is None:
    print("Zenoss.cse directory not found", file=sys.stderr)
    sys.exit(1)

# services_tree = next((t for t in root.trees if t.name == "services"), None)
# if services_tree is None:
#     print("services directory not found", file=sys.stderr)
#     sys.exit(1)

# cse_tree = next(
#     (t for t in services_tree.trees if t.name == "Zenoss.cse"),
#     None,
# )
# if cse_tree is None:
#     print("Zenoss.cse directory not found", file=sys.stderr)
#     sys.exit(1)

print("-" * 100)
for entry in cse_tree.traverse():
    entrypath = Path(entry.path)
    if entry.type == "tree":
        directory = service_dump_path.joinpath(*entrypath.parts[2:])
        directory.mkdir(parents=True, exist_ok=True)
    elif entry.type == "blob":
        try:
            filename = service_dump_path.joinpath(*entrypath.parts[2:])
            with filename.open("w+b") as f:
                entry.stream_data(f)
        except Exception as ex:
            print(ex)
            print(entry.path)
            print(filename)
            sys.exit(1)
    else:
        print(entry.type)
        print(dir(entry))

# for path in list_paths(cse_tree):
#     print(path)
#     print(repo.git.show(
#         "{}:{}".format(
#             prior_tag,
#             "services/Zenoss.cse/{}".format(path),
#         ),
#     ))
#     sys.exit(0)
# git = repo.git
# repo_path = "%s:services/Zenoss.cse" % prior
# for filename in git.ls_tree("-r", "--name-only", repo_path):
#     print(type(filename), len(filename))

prior_template = test_output / "prior_template.json"
prior_definitions = test_output / "prior_definitions.json"

compiled = subprocess.run(
    ["serviced-service", "compile", str(service_dump_path)],
    capture_output=True,
)
if compiled.returncode == 0:
    with open(prior_template, "w+b") as f:
        f.write(compiled.stdout)

deployed = subprocess.run(
    ["serviced-service", "deploy", str(prior_template)],
    capture_output=True,
)
if deployed.returncode == 0:
    with open(prior_definitions, "w+b") as f:
        f.write(deployed.stdout)
