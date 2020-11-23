from __future__ import print_function

import os
import sys
from setuptools import setup, find_packages

_version = os.environ.get("VERSION")
if _version is None:
    print("VERSION environment variable not found", file=sys.stderr)
    sys.exit(1)


setup(
    name="zenservicemigration",
    version=_version,
    description="Zenoss Service Definition Migration Scripts",
    author="Zenoss, Inc.",
    url="https://www.zenoss.com",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    package_data={
        "zenservicemigration": [
                "migrations/*.py",
                "migrations/data/*",
                "migrations/data/zenhubworker_user/*"
        ],
    },
    zip_safe=False,
    install_requires=["servicemigration"],
    python_requires=">=2.7,<3",
    entry_points={
        "console_scripts": [
            "zensvcmigrate=zenservicemigration.migrate:main",
        ],
    },
)
