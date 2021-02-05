##############################################################################
#
# Copyright (C) Zenoss, Inc. 2021, all rights reserved.
#
# This content is made available according to terms specified in
# License.zenoss under the directory where your Zenoss product is installed.
#
##############################################################################

"""
Further update zing-connector config to support compact-metrics.
"""

from __future__ import print_function

import sys

import servicemigration as sm

version = "7.0.19"


def migrate(ctx, *args, **kw):
    service = next((s for s in ctx.services if s.name == "zing-connector"), None)
    if service is None:
        print("No zing-connector services found.", file=sys.stderr)
        return False

    service.endpoints = [ep for ep in service.endpoints[:] if ep.application != "zing-connector-admin"]

    new_script="test \"$(/opt/zenoss/bin/hctest 9237)\" = \"PONG\""

    answering = next((hc for hc in service.healthChecks if hc.name == "answering"), None)

    if answering is None:
        print("Adding missing 'answering' healthcheck")
        answering = sm.HealthCheck(
            name="answering",
            script=new_script,
            interval=5.0,
        )

    if answering.script != new_script:
        answering.script = new_script
        print("Updated 'answering' healthcheck script.")

    service.healthChecks = [answering]

    return True
