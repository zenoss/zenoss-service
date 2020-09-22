##############################################################################
#
# Copyright (C) Zenoss, Inc. 2020, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

from __future__ import print_function

import sys

version = "7.0.16"


def migrate(ctx, *args, **kw):

    changes = []

    for svc_name in (
        "zendebug", "metric_shipper", "zing-api-proxy", "zing-connector",
    ):
        service = next(
            (s for s in ctx.services if s.name == svc_name),
            None,
        )
        if service is None:
            print("%s service not found.".format(svc_name), file=sys.stderr)
            continue

        changes.append(_updateStartup(service))
        changes.append(_updateRunAs(service))

    return any(changes)


class _MigrationData(object):

    startup_command = {
        "zendebug": (
            "/opt/zenoss/zopehome/runzope -C /opt/zenoss/etc/zendebug.conf"
        ),
        "metric_shipper": (
            "cd /opt/zenoss && "
            "/bin/supervisord -n -c etc/metricshipper/supervisord.conf"
        ),
        "zing-api-proxy": (
            "cd /opt/zenoss && "
            "/bin/supervisord -n -c etc/api-key-proxy/supervisord.conf"
        ),
        "zing-connector": (
            "cd /opt/zenoss && "
            "/bin/supervisord -n -c etc/zing-connector/supervisord.conf"
        ),
    }


migrationData = _MigrationData()


def _updateStartup(service):
    command = migrationData.startup_command[service.name]
    if service.startup != command:
        service.startup = command
        print("Updated %s startup command".format(service.name))
        return True
    return False


def _updateRunAs(service):
    if service.runAs != "zenoss":
        service.runAs = "zenoss"
        print("Updated %s RunAs field".format(service.name))
        return True
    return False
