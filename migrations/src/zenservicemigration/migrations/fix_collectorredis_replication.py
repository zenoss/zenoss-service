##############################################################################
#
# Copyright (C) Zenoss, Inc. 2020, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

"""
Change the collectorredis command to reliably enable replication.
"""

from __future__ import print_function

import sys

version = "6.6.0"

_command = (
    "/usr/bin/redis-server /etc/redis.conf"
    "{{if ne .InstanceID 0}} --slaveof rd1 6379{{end}}"
)


def migrate(ctx, *args, **kw):
    services = [s for s in ctx.services if s.name == "collectorredis"]
    if not services:
        print("No collectorredis services found.", file=sys.stderr)
        return False

    needs_update = [s for s in services if s.startup != _command]
    if not needs_update:
        print(
            "All {} collectorredis services already updated."
            .format(len(services))
        )
        return False

    already_updated_count = len(services) - len(needs_update)
    if already_updated_count > 0:
        print(
            "{} collectorredis services already updated"
            .format(already_updated_count)
        )

    changed = False
    for service in needs_update:
        if service.startup != _command:
            service.startup = _command
            changed = True
    print("Updated {} collectorredis services.".format(len(needs_update)))

    return changed
