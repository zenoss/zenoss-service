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

version = "7.0.20"


other_services = (
        "zenhubiworker",
        "zenhubworker (adm)",
        "zenhubworker (default)",
        "zenhubworker (user)",
        "zenhub",
        "MetricConsumer",
        "Zope",
        "zenapi",
        "zendebug",
        "zenjobs",
        )

new_script="test \"$(/opt/zenoss/bin/healthchecks/zing_connector_answering 9237)\" = \"PONG\""

def migrate(ctx, *args, **kw):
    service = next((s for s in ctx.services if s.name == "zing-connector"), None)
    if service is None:
        print("No zing-connector services found.", file=sys.stderr)
        return False

    answering = next((hc for hc in service.healthChecks if hc.name == "answering"), None)
    if answering is None:
        print("No answering healthcheck is found, and it should have been installed by update_zing_connector_config_for_compact_second.py. Make sure that is run first.", file=sys.stderr)
        return False

    changed = False

    if answering.script != new_script:
        answering.script = new_script
        print("Updated 'answering' healthcheck script for zing-connector service.", file=sys.stderr)
        service.healthChecks = [answering]
        changed = True

    for svc in other_services:
        changed = changed or remove_endpoint_and_fix_hc(svc)

    return changed


def remove_endpoint_and_fix_hc(svc):
    """
    remove the zing-connector-admin endpoint and maybe update the zing-connector-answering healthcheck script
    """
    service = next((s for s in ctx.services if s.name == svc), None)
    if service is None:
        print("No {} service found, so did not remove endpoint.".format(svc), file=sys.stderr)
        return False

    initialLength = len(service.endpoints)
    service.endpoints = [ep for ep in service.endpoints[:] if ep.application != "zing-connector-admin"]

    changed = len(service.endpoints) < initialLength
    print("{} zing-connector-admin endpoint from {} service".format("Removed" if changed else "Did NOT remove", svc), file=sys.stderr)

    answering = next((hc for hc in service.healthChecks if hc.name == "zing-connector-answering"), None)

    # not all these services have the healthcheck
    if answering and answering.script != new_script:
        answering.script = new_script
        print("Updated 'zing-connector-answering' healthcheck script for {} service.".format(svc), file=sys.stderr)
        service.healthChecks = [answering]
        changed = True

    return changed
